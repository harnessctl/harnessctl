import httpx
from typing import List
from harnessctl.discovery.base import DiscoveredModel, RuntimeProbe


class OpenAICompatProbe(RuntimeProbe):
    def __init__(self, runtime: str, endpoint: str):
        self.runtime = runtime
        self.endpoint = endpoint.rstrip("/")

    async def probe(self) -> List[DiscoveredModel]:
        url = f"{self.endpoint}/models"
        models = []
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                for model in data.get("data", []):
                    if "id" in model:
                        models.append(
                            DiscoveredModel(
                                runtime=self.runtime,
                                id=model["id"],
                                endpoint=self.endpoint,
                            )
                        )
            except Exception:
                raise
        return models
