import asyncio
import os
from typing import List
from harnessctl.discovery.base import RuntimeProbe, DiscoveredModel
from harnessctl.providers.manager import SecretsManager


class OpencodeProbe(RuntimeProbe):
    """
    Discovers models available via the 'opencode models' command.
    This effectively bridges tokens and configuration managed by opencode.
    """

    def __init__(self):
        super().__init__()
        self.secrets = SecretsManager()

    async def probe(self) -> List[DiscoveredModel]:
        try:
            # Inject tokens from SecretsManager into environment for opencode
            env = os.environ.copy()
            github_token = self.secrets.get_token("github")
            if github_token:
                env["GITHUB_TOKEN"] = github_token

            process = await asyncio.create_subprocess_exec(
                "opencode",
                "models",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            stdout, _ = await process.communicate()

            if process.returncode != 0:
                return []

            models = []
            for line in stdout.decode().splitlines():
                model_id = line.strip()
                if not model_id:
                    continue

                # Heuristic: Determine provider from prefix
                provider = "opencode"
                if "/" in model_id:
                    provider = model_id.split("/")[0]

                models.append(
                    DiscoveredModel(
                        runtime="opencode",
                        id=model_id,
                        endpoint="opencode",  # Virtual endpoint
                        local=False,  # opencode models are usually remote/cloud
                        metadata={"provider": provider},
                    )
                )
            return models
        except Exception:
            return []
