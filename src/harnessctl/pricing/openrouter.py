from typing import Dict, Any
from harnessctl.pricing.cache import write_cache
from harnessctl.pricing.common import fetch_prices_generic
from harnessctl.spec.warnings import WarningCollector

URL = "https://openrouter.ai/api/v1/models"


async def fetch_openrouter_prices(
    warnings: WarningCollector, force_refresh: bool = False
) -> Dict[str, Any]:
    data = await fetch_prices_generic(
        "openrouter", URL, warnings, force_refresh=force_refresh
    )
    if data is None:
        return {}

    result = {}
    models_data = data.get("data", [])
    for item in models_data:
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
