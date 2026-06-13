from typing import List, Dict, Any, Tuple
from harnessctl.pricing.catalog import MarketModel
from harnessctl.pricing.common import fetch_prices_generic
from harnessctl.spec.warnings import WarningCollector
from harnessctl.pricing.heuristics import (
    get_intel_heuristic,
    get_speed_heuristic,
    get_pricing_heuristic,
)

OPENROUTER_URL = "https://openrouter.ai/api/v1/models"


def get_intelligence_score(model_data: Dict[str, Any]) -> Tuple[float, str]:
    """Extract intelligence score and source from OpenRouter benchmarks."""
    model_id = model_data.get("id", "")
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

    # Priority 3: Name-based High-Confidence Matching (Not "guessing")
    # If the ID clearly identifies a SOTA class, we give it a heuristic score.
    # This allows discovered official models (github, google) to be ranked.
    score = get_intel_heuristic(model_id)
    if score > 0:
        return score, "heuristic"

    # Priority 4: Default/Unknown
    return 0.0, "heuristic"


def get_speed_score(model_data: Dict[str, Any]) -> float:
    """Estimate speed (TPS) for commercial models."""
    return get_speed_heuristic(model_data.get("id", ""))


async def fetch_openrouter_market(
    warnings: WarningCollector, force_refresh: bool = False
) -> List[MarketModel]:
    """Fetch and process global market data from OpenRouter."""
    from harnessctl.providers.manager import SecretsManager

    secrets = SecretsManager()
    token = secrets.get_token("openrouter")

    if not token:
        warnings.add(
            field="openrouter_market",
            reason="API key missing. Discovery skipped.",
        )
        return []

    data = await fetch_prices_generic(
        "openrouter_market",
        OPENROUTER_URL,
        warnings,
        force_refresh=force_refresh,
        headers={"Authorization": f"Bearer {token}"},
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
    from harnessctl.pricing.github import (
        fetch_github_models_market,
        fetch_github_copilot_market,
    )
    from harnessctl.pricing.google import fetch_google_market

    tasks = [
        fetch_openrouter_market(warnings, force_refresh),
        fetch_litellm_market(warnings, force_refresh),
        fetch_github_models_market(warnings, force_refresh),
        fetch_github_copilot_market(warnings, force_refresh),
        fetch_google_market(warnings, force_refresh),
    ]

    results = await asyncio.gather(*tasks)

    # Merge and deduplicate (Strategic merging)
    catalog: Dict[str, MarketModel] = {}

    def merge_model(new_model: MarketModel):
        existing = catalog.get(new_model.id)
        if not existing:
            # Try fuzzy matching for official models without provider prefix
            # e.g. gemini-2.0-flash (from LiteLLM) matches google/gemini-2.0-flash
            for prefix in [
                "google/",
                "github/",
                "github-copilot/",
                "openai/",
                "anthropic/",
            ]:
                if new_model.id.startswith(prefix):
                    base_id = new_model.id.split("/", 1)[1]
                    if base_id in catalog:
                        existing = catalog[base_id]
                        break
                else:
                    prefixed_id = f"google/{new_model.id}"  # Try google as common case
                    if prefixed_id in catalog:
                        existing = catalog[prefixed_id]
                        break

            if not existing:
                if new_model.input_per_mtok == 0 and new_model.output_per_mtok == 0:
                    new_model.input_per_mtok, new_model.output_per_mtok = (
                        get_pricing_heuristic(new_model.id)
                    )
                catalog[new_model.id] = new_model
                return

        # If existing has a price and new one doesn't, keep the price
        if (
            existing.input_per_mtok > 0 or existing.output_per_mtok > 0
        ) and new_model.input_per_mtok == 0:
            new_model.input_per_mtok = existing.input_per_mtok
            new_model.output_per_mtok = existing.output_per_mtok

        # Final pricing heuristic if still zero after merging
        if new_model.input_per_mtok == 0 and new_model.output_per_mtok == 0:
            new_model.input_per_mtok, new_model.output_per_mtok = get_pricing_heuristic(
                new_model.id
            )

        # If existing has better intelligence source, keep it
        if (
            existing.intelligence_source in ["benchmark", "elo"]
            and new_model.intelligence_source == "heuristic"
        ):
            new_model.intelligence = existing.intelligence
            new_model.intelligence_source = existing.intelligence_source

        # If existing has context window and new one doesn't
        if existing.context_window > 0 and new_model.context_window == 0:
            new_model.context_window = existing.context_window

        catalog[new_model.id] = new_model

    # Order of merging defines "officialness" (last source wins for metadata, but we preserve prices/benchmarks)
    # 1. LiteLLM (Broadest pricing/context data)
    for model in results[1]:
        merge_model(model)

    # 2. Google (Official discovery)
    for model in results[4]:
        merge_model(model)

    # 3. GitHub (Official discovery)
    for res_idx in [2, 3]:
        for model in results[res_idx]:
            merge_model(model)

    # 4. OpenRouter (Premium metadata & Benchmarks)
    for model in results[0]:
        merge_model(model)

    return list(catalog.values())
