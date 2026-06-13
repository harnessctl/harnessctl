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
        async with httpx.AsyncClient(timeout=2.0) as client:
            try:
                response = await client.get(url)
                if response.status_code != 200:
                    return []
                data = response.json()
                # LM Studio sometimes returns a list directly or a dict with "data"
                model_list = data.get("data", []) if isinstance(data, dict) else data
                if not isinstance(model_list, list):
                    return []

                for model in model_list:
                    if isinstance(model, dict) and "id" in model:
                        models.append(
                            DiscoveredModel(
                                runtime=self.runtime,
                                id=model["id"],
                                endpoint=self.endpoint,
                            )
                        )
            except Exception:
                return []
        return models
