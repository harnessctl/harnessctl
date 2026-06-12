from typing import Dict, Any
from harnessctl.pricing.cache import write_cache
from harnessctl.pricing.common import fetch_prices_generic
from harnessctl.spec.warnings import WarningCollector

URL = "https://raw.githubusercontent.com/BerriAI/litellm/main/model_prices_and_context_window.json"


async def fetch_litellm_prices(
    warnings: WarningCollector, force_refresh: bool = False
) -> Dict[str, Any]:
    data = await fetch_prices_generic(
        "litellm", URL, warnings, force_refresh=force_refresh
    )
    if data is None:
        return {}

    result = {}
    for model_id, info in data.items():
        if (
            isinstance(info, dict)
            and "input_cost_per_token" in info
            and "output_cost_per_token" in info
        ):
            # litellm gives price per token, we want per million
            try:
                input_per_mtok = float(info["input_cost_per_token"]) * 1_000_000
                output_per_mtok = float(info["output_cost_per_token"]) * 1_000_000
                context_window = info.get("max_tokens", 0) or info.get(
                    "max_input_tokens", 0
                )

                result[model_id] = {
                    "input_per_mtok": input_per_mtok,
                    "output_per_mtok": output_per_mtok,
                    "context_window": context_window,
                    "provider": "litellm",
                }
            except (ValueError, TypeError):
                pass

    write_cache("litellm", result)
    return result
