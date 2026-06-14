from typing import List, Optional
from dataclasses import dataclass
from huggingface_hub import HfApi
from harnessctl.recommend.estimate import estimate_footprint, fits_in_memory
from harnessctl.recommend.intent import TaskIntent
from harnessctl.sysprobe.profile import SystemProfile
from harnessctl.pricing.market import MarketModel


@dataclass
class RankedModel:
    id: str  # Can be repo_id or Cloud ID
    provider: str  # "huggingface", "google", "openrouter", etc.
    quant: Optional[str]
    params_billion: Optional[float]
    estimated_memory_gb: Optional[float]
    backend: str  # "llama.cpp", "cloud"
    score: float
    is_cloud: bool = False
    intelligence: float = 0.0
    intelligence_source: str = "heuristic"
    speed_tps: float = 0.0
    input_per_mtok: float = 0.0
    output_per_mtok: float = 0.0
    context_window: int = 4096


def search_candidates(
    profile: SystemProfile,
    intent: TaskIntent,
    market_data: List[MarketModel] = [],
    include_local: bool = True,
    include_commercial: bool = True,
    provider_filter: Optional[str] = None,
    grep: Optional[str] = None,
    limit: int = 10,
    trusted_only: bool = False,
) -> List[RankedModel]:
    """Search and rank models based on system fit, intent, and market availability."""
    candidates = []

    trusted_fn = None
    if trusted_only:
        from harnessctl.recommend.trusted import is_trusted_author

        trusted_fn = is_trusted_author

    # 1. Local Search (HuggingFace)
    if include_local:
        if provider_filter and "huggingface" not in provider_filter.lower():
            pass  # Skip if provider filtered and not HF
        else:
            api = HfApi()
            tags = ["gguf", "instruct"]
            if intent.is_coding:
                tags.append("coding")

            # Adjust search based on complexity and grep
            search_limit = max(limit * 4, 100)
            if intent.complexity > 60:
                search_limit *= 2

            models = api.list_models(
                filter=tags,
                search=grep if grep else None,
                sort="downloads",
                limit=search_limit,
            )

            for model in models:
                if trusted_fn and not trusted_fn(model.modelId):
                    continue
                try:
                    # Check for GGUF files
                    files = api.list_repo_files(model.modelId)
                    gguf_files = [f for f in files if f.endswith(".gguf")]
                    if not gguf_files:
                        continue

                    available_quants = []
                    for f in gguf_files:
                        for q in ["Q4_K_M", "Q5_K_M", "Q6_K", "Q8_0", "F16"]:
                            if q in f:
                                available_quants.append((q, f))
                                break

                    if not available_quants:
                        continue

                    params_billion = 7.0
                    import re

                    m = re.search(r"(\d+(\.\d+)?)b", model.modelId.lower())
                    if m:
                        params_billion = float(m.group(1))

                    for quant, _ in available_quants:
                        if fits_in_memory(profile, int(params_billion), quant):
                            est_gb = estimate_footprint(int(params_billion), quant)
                            from harnessctl.recommend.estimate import QUANT_BITS

                            # Base score on params and bit depth
                            score = params_billion * QUANT_BITS.get(quant, 4.0)

                            # Complexity adjustment: High complexity tasks penalize small models
                            if intent.complexity > 70 and params_billion < 10:
                                score *= 0.5

                            if intent.is_coding:
                                if any(
                                    k in model.modelId.lower()
                                    for k in ["coder", "code", "instruct-qa"]
                                ):
                                    score *= 2.5
                                else:
                                    score *= 1.5

                            from harnessctl.pricing.catalog import (
                                estimate_local_metrics,
                            )

                            intel, speed = estimate_local_metrics(model.modelId)

                            candidates.append(
                                RankedModel(
                                    id=model.modelId,
                                    provider="huggingface",
                                    quant=quant,
                                    params_billion=params_billion,
                                    estimated_memory_gb=est_gb,
                                    backend="llama.cpp",
                                    score=score,
                                    is_cloud=False,
                                    intelligence=intel,
                                    intelligence_source="heuristic",
                                    speed_tps=speed,
                                    context_window=32768,
                                    input_per_mtok=0.0,
                                    output_per_mtok=0.0,
                                )
                            )
                except Exception:
                    continue

    # 2. Cloud Search (Market)
    if include_commercial:
        for m in market_data:
            if provider_filter and provider_filter.lower() not in m.provider.lower():
                continue

            if (
                grep
                and grep.lower() not in m.id.lower()
                and grep.lower() not in m.name.lower()
            ):
                continue

            # Cloud Search matches are also filtered by intelligence unless
            # we are explicitly searching/grepping or have a high limit
            threshold = 50
            if grep or provider_filter or limit > 50:
                threshold = 0

            if m.intelligence < threshold and not (
                grep
                and (grep.lower() in m.id.lower() or grep.lower() in m.name.lower())
            ):
                continue

            # In ranker, we must ensure we don't accidentally skip $0.00 price models
            # when calculating price_factor (avoid division by zero if it happens,
            # though we added +0.05)

            # Score based on intelligence and alignment with intent
            score = m.intelligence * 1.5

            # Complexity Alignment
            if intent.complexity > 50:
                if m.intelligence > 90:
                    score *= 3.0  # Massive bonus for SOTA on complex tasks
                elif m.intelligence < 80:
                    score *= 0.3  # Penalize mid-tier models for high complexity

            # 1. Reasoning Preference
            if intent.prefers_reasoning:
                if any(k in m.id.lower() for k in ["o1", "r1", "thought", "reasoning"]):
                    score *= 5.0  # High priority for reasoning models
                elif m.intelligence < 90:
                    score *= 0.5  # De-prioritize lower intel for reasoning

            # 2. Cheap Preference
            if intent.prefers_cheap:
                # Factor in price: lower is better.
                # Normalize against a "reasonable" price of $1.00
                price_factor = 1.0 / (m.input_per_mtok + 0.05)
                score *= price_factor * 0.5  # Blend price into score

            # 3. Speed Preference
            if intent.prefers_speed:
                if m.speed_tps > 100:
                    score *= 2.0
                elif m.speed_tps < 30:
                    score *= 0.5

            if intent.is_coding:
                if any(k in m.id.lower() for k in ["coder", "code", "instruct-qa"]):
                    score *= 2.5
                else:
                    score *= 1.5

            candidates.append(
                RankedModel(
                    id=m.id,
                    provider=m.provider,
                    quant=None,
                    params_billion=None,
                    estimated_memory_gb=0,
                    backend="cloud",
                    score=score,
                    is_cloud=True,
                    intelligence=m.intelligence,
                    intelligence_source=m.intelligence_source,
                    speed_tps=m.speed_tps,
                    input_per_mtok=m.input_per_mtok,
                    output_per_mtok=m.output_per_mtok,
                    context_window=m.context_window,
                )
            )

    # Final Ranking and Deduplication
    candidates.sort(key=lambda x: x.score, reverse=True)

    seen_ids = set()
    final_results = []
    # If we are searching or sorting by something else, we want a larger pool
    # before we apply the final 'limit' from this function's perspective.
    # Actually, the caller handles the final display limit.
    # So we should return a healthy amount of candidates.

    internal_limit = max(limit * 2, 100)
    if grep:
        internal_limit = max(internal_limit, 500)

    for c in candidates:
        if c.id not in seen_ids:
            seen_ids.add(c.id)
            final_results.append(c)
            if len(final_results) >= internal_limit:
                break

    return final_results
