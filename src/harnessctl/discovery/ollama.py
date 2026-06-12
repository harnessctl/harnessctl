import httpx
from typing import List
from harnessctl.discovery.base import DiscoveredModel, RuntimeProbe


class OllamaProbe(RuntimeProbe):
    def __init__(self, endpoint: str = "http://localhost:11434"):
        self.endpoint = endpoint.rstrip("/")

    async def probe(self) -> List[DiscoveredModel]:
        url = f"{self.endpoint}/api/tags"
        models = []
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                for model in data.get("models", []):
                    if "name" in model:
                        models.append(
                            DiscoveredModel(
                                runtime="ollama",
                                id=model["name"],
                                endpoint=self.endpoint,
                            )
                        )
            except Exception:
                raise
        return models
