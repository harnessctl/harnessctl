import httpx
from typing import Dict, Any
from harnessctl.pricing.cache import read_cache, read_stale_cache, write_cache
from harnessctl.spec.warnings import WarningCollector

URL = "https://openrouter.ai/api/v1/models"


async def fetch_openrouter_prices(
    warnings: WarningCollector, force_refresh: bool = False
) -> Dict[str, Any]:
    if not force_refresh:
        cached = read_cache("openrouter", ttl_hours=24)
        if cached is not None:
            return cached

    result = {}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(URL, timeout=10)
            response.raise_for_status()
            data = response.json().get("data", [])

            for item in data:
                model_id = item.get("id")
                pricing = item.get("pricing", {})

                try:
                    # openrouter gives price per token as string usually
                    input_per_mtok = float(pricing.get("prompt", 0)) * 1_000_000
                    output_per_mtok = float(pricing.get("completion", 0)) * 1_000_000
                    context_window = item.get("context_length", 0)

                    result[model_id] = {
                        "input_per_mtok": input_per_mtok,
                        "output_per_mtok": output_per_mtok,
                        "context_window": context_window,
                        "provider": "openrouter",
                    }
                except (ValueError, TypeError):
                    pass

            write_cache("openrouter", result)
            return result
        except Exception as e:
            warnings.add_warning(
                f"Failed to fetch openrouter prices: {e}. Falling back to stale cache."
            )
            stale = read_stale_cache("openrouter")
            return stale if stale is not None else {}
