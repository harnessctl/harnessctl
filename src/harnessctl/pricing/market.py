from typing import List, Dict, Any, Tuple
from harnessctl.pricing.catalog import MarketModel
from harnessctl.pricing.common import fetch_prices_generic
from harnessctl.spec.warnings import WarningCollector

OPENROUTER_URL = "https://openrouter.ai/api/v1/models"


def get_intelligence_score(model_data: Dict[str, Any]) -> Tuple[float, str]:
    """Extract intelligence score and source from OpenRouter benchmarks."""
    benchmarks = model_data.get("benchmarks", {})
    aa = benchmarks.get("artificial_analysis", {})

    # Priority 1: Artificial Analysis Intelligence Index
    intel = aa.get("intelligence_index")
    if intel is not None:
        # Artificial Analysis Intelligence Index normalization.
        # 65 (SOTA) -> ~98
        val = float(intel)
        return min(99.0, val * 1.5), "benchmark"

    # Priority 2: Design Arena ELO (Normalized)
    da = benchmarks.get("design_arena")
    if isinstance(da, list) and len(da) > 0:
        # OpenRouter returns a list of arena categories
        # We'll take the max ELO found across categories
        elos = [float(item["elo"]) for item in da if "elo" in item]
        if elos:
            max_elo = max(elos)
            # Normalize: 1000 (Base) -> 1300+ (SOTA)
            # (1300 - 1000) / 3.2 = 93.75
            score = max(0.0, min(100.0, (max_elo - 1000) / 3.2))
            return score, "elo"

    # Priority 3: Name-based heuristics (Last resort)
    name = model_data.get("id", "").lower()
    if any(
        k in name
        for k in [
            "o1",
            "claude-3-5",
            "fable",
            "gpt-4o",
            "deepseek-v3",
            "deepseek-r1",
            "gemini-2.0",
        ]
    ):
        return 95.0, "heuristic"
    if any(
        k in name
        for k in ["opus", "gpt-4", "llama-3.1-405b", "smaug", "gemini-1.5-pro"]
    ):
        return 90.0, "heuristic"
    if any(
        k in name for k in ["sonnet", "llama-3.1-70b", "qwen2.5-72b", "deepseek-v2.5"]
    ):
        return 80.0, "heuristic"
    if any(k in name for k in ["haiku", "flash", "mini", "8b", "llama-3.1-8b"]):
        return 55.0, "heuristic"
    if any(k in name for k in ["coder", "qwen", "gemma"]):
        return 65.0, "heuristic"

    return 40.0, "heuristic"


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


async def fetch_openrouter_market(
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

            intel, intel_src = get_intelligence_score(item)
            market_models.append(
                MarketModel(
                    id=model_id,
                    name=item.get("name", model_id),
                    provider="openrouter",
                    input_per_mtok=input_per_mtok,
                    output_per_mtok=output_per_mtok,
                    context_window=item.get("context_length", 0),
                    intelligence=intel,
                    intelligence_source=intel_src,
                    speed_tps=get_speed_score(item),
                    local=False,
                    status="available",
                )
            )
        except (ValueError, TypeError):
            continue

    return market_models


async def fetch_litellm_market(
    warnings: WarningCollector, force_refresh: bool = False
) -> List[MarketModel]:
    """Fetch and process global market data from LiteLLM's huge registry."""
    from harnessctl.pricing.litellm import URL as LITELLM_URL
    from harnessctl.pricing.cache import write_cache

    data = await fetch_prices_generic(
        "litellm_market", LITELLM_URL, warnings, force_refresh=force_refresh
    )

    if not data:
        return []

    # Persist LiteLLM market data to cache
    write_cache("litellm_market", data)

    market_models = []
    # LiteLLM format is { "model_id": { ...info... } }
    for model_id, info in data.items():
        if not isinstance(info, dict):
            continue

        # Skip models that are obviously local or incomplete
        if "input_cost_per_token" not in info:
            continue

        try:
            input_per_mtok = float(info.get("input_cost_per_token", 0)) * 1_000_000
            output_per_mtok = float(info.get("output_cost_per_token", 0)) * 1_000_000
            try:
                context_window_raw = info.get("max_tokens", 0) or info.get(
                    "max_input_tokens", 0
                )
                context_window = (
                    int(context_window_raw)
                    if isinstance(context_window_raw, (int, float, str))
                    and str(context_window_raw).isdigit()
                    else 0
                )
            except (ValueError, TypeError):
                context_window = 0

            # Map LiteLLM provider
            provider = info.get("litellm_provider", "commercial")
            intel, intel_src = get_intelligence_score({"id": model_id})

            market_models.append(
                MarketModel(
                    id=model_id,
                    name=model_id,
                    provider=provider,
                    input_per_mtok=input_per_mtok,
                    output_per_mtok=output_per_mtok,
                    context_window=context_window,
                    # For LiteLLM, we only have name-based heuristics
                    intelligence=intel,
                    intelligence_source=intel_src,
                    speed_tps=get_speed_score({"id": model_id}),
                    local=False,
                    status="available",
                )
            )
        except (ValueError, TypeError):
            continue

    return market_models


async def fetch_market_data(
    warnings: WarningCollector, force_refresh: bool = False
) -> List[MarketModel]:
    """Aggregate market data from multiple sources."""
    import asyncio

    tasks = [
        fetch_openrouter_market(warnings, force_refresh),
        fetch_litellm_market(warnings, force_refresh),
    ]

    results = await asyncio.gather(*tasks)

    # Merge and deduplicate (OpenRouter takes priority for better metadata)
    catalog: Dict[str, MarketModel] = {}

    # Load LiteLLM first (base)
    for model in results[1]:
        catalog[model.id] = model

    # Overwrite with OpenRouter (enriched)
    for model in results[0]:
        catalog[model.id] = model

    return list(catalog.values())
