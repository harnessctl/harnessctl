from typing import List, Dict, Any
from harnessctl.pricing.catalog import MarketModel
from harnessctl.pricing.common import fetch_prices_generic
from harnessctl.spec.warnings import WarningCollector

OPENROUTER_URL = "https://openrouter.ai/api/v1/models"


def get_intelligence_score(model_data: Dict[str, Any]) -> float:
    """Extract intelligence score from OpenRouter benchmarks."""
    benchmarks = model_data.get("benchmarks", {})
    aa = benchmarks.get("artificial_analysis", {})

    # Priority 1: Artificial Analysis Intelligence Index
    intel = aa.get("intelligence_index")
    if intel is not None:
        # OpenRouter returns the raw index value.
        # According to AA methodology, this is often a percentage (0-100).
        # We'll treat it as such.
        return float(intel)

    # Priority 2: Design Arena ELO (Normalized)
    da = benchmarks.get("design_arena")
    if isinstance(da, dict) and da.get("elo") is not None:
        elo = float(da["elo"])
        return max(0.0, min(100.0, (elo - 1000) / 4))

    # Priority 3: Name-based heuristics (Last resort)
    name = model_data.get("id", "").lower()
    if any(k in name for k in ["o1", "claude-3-5", "gpt-4o"]):
        return 90.0
    if any(k in name for k in ["opus", "gpt-4"]):
        return 85.0
    if any(k in name for k in ["sonnet", "gemini-1.5-pro", "llama-3.1-70b"]):
        return 75.0
    if any(k in name for k in ["mini", "flash", "haiku", "8b"]):
        return 50.0

    return 40.0


def get_speed_score(model_data: Dict[str, Any]) -> float:
    """Estimate speed (TPS) for commercial models."""
    # Since OpenRouter doesn't provide numeric TPS, we use heuristics
    # based on model class/name.
    name = model_data.get("id", "").lower()

    if any(k in name for k in ["mini", "flash", "haiku", "8b"]):
        return 150.0
    if any(k in name for k in ["sonnet", "4o", "70b"]):
        return 70.0
    if any(k in name for k in ["opus", "o1", "405b"]):
        return 15.0

    return 40.0


async def fetch_market_data(
    warnings: WarningCollector, force_refresh: bool = False
) -> List[MarketModel]:
    """Fetch and process global market data from OpenRouter."""
    data = await fetch_prices_generic(
        "openrouter_market", OPENROUTER_URL, warnings, force_refresh=force_refresh
    )

    if not data or "data" not in data:
        return []

    market_models = []
    for item in data["data"]:
        model_id = item.get("id")
        pricing = item.get("pricing", {})

        try:
            input_per_mtok = float(pricing.get("prompt", 0)) * 1_000_000
            output_per_mtok = float(pricing.get("completion", 0)) * 1_000_000

            market_models.append(
                MarketModel(
                    id=model_id,
                    name=item.get("name", model_id),
                    provider="openrouter",
                    input_per_mtok=input_per_mtok,
                    output_per_mtok=output_per_mtok,
                    context_window=item.get("context_length", 0),
                    intelligence=get_intelligence_score(item),
                    speed_tps=get_speed_score(item),
                    local=False,
                    status="available",
                )
            )
        except (ValueError, TypeError):
            continue

    return market_models
