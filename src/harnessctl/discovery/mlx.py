import platform
import os
from pathlib import Path
from typing import List
from harnessctl.discovery.base import DiscoveredModel, RuntimeProbe
from harnessctl.discovery.openai_compat import OpenAICompatProbe


class MLXProbe(RuntimeProbe):
    def __init__(self, endpoint: str = "http://localhost:8080/v1"):
        self.endpoint = endpoint.rstrip("/")
        self.api_probe = OpenAICompatProbe(runtime="mlx", endpoint=self.endpoint)

    async def probe(self) -> List[DiscoveredModel]:
        if platform.system() != "Darwin":
            return []

        models = []

        # 1. API probe
        try:
            api_models = await self.api_probe.probe()
            models.extend(api_models)
        except Exception:
            pass

        # 2. Cache scan
        cache_dir = Path(os.path.expanduser("~/.cache/huggingface/hub"))
        if cache_dir.exists() and cache_dir.is_dir():
            for entry in cache_dir.iterdir():
                if entry.is_dir() and entry.name.startswith("models--"):
                    # models--org--repo -> org/repo
                    parts = entry.name.split("--")[1:]
                    if parts:
                        model_id = "/".join(parts)
                        models.append(
                            DiscoveredModel(
                                runtime="mlx", id=model_id, endpoint=self.endpoint
                            )
                        )

        # deduplicate
        seen = set()
        unique = []
        for m in models:
            if m.id not in seen:
                seen.add(m.id)
                unique.append(m)
        return unique
