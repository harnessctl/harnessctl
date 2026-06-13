import math
from typing import List, Dict
from dataclasses import dataclass
from harnessctl.pricing.catalog import MarketModel
from harnessctl.sysprobe.profile import SystemProfile
from harnessctl.recommend.estimate import estimate_footprint


@dataclass
class RecommendationProfile:
    name: str
    intel_weight: float
    speed_weight: float
    price_weight: float


PROFILES = {
    "coding": RecommendationProfile("coding", 1.5, 0.8, 1.0),
    "reasoning": RecommendationProfile("reasoning", 2.0, 0.5, 1.0),
    "chat": RecommendationProfile("chat", 1.0, 1.0, 1.0),
    "fast": RecommendationProfile("fast", 0.5, 2.0, 0.8),
}


class RecommendationEngine:
    def __init__(self, profile: SystemProfile):
        self.sys_profile = profile

    def score_model(
        self, model: MarketModel, task_profile: RecommendationProfile
    ) -> float:
        """Calculate a unified value score for a model."""
        # 1. Normalize Intelligence (0-100 -> 0-1)
        norm_intel = model.intelligence / 100.0

        # 2. Normalize Speed (0-200 TPS -> 0-1)
        # We cap at 200 as anything above is "instant" for human perception
        norm_speed = min(model.speed_tps, 200.0) / 200.0

        # 3. Normalize Price
        # Lower price is better. Local models (0.0) should get max score.
        # We use a log scale to handle the wide range of commercial prices.
        if model.local or model.output_per_mtok == 0:
            norm_price = 1.0
        else:
            # Typical range: $0.01 to $100+ per MTok
            # log10(0.01) = -2, log10(100) = 2
            # We shift it to 0-4 range and invert
            price_log = math.log10(max(0.001, model.output_per_mtok))
            norm_price = 1.0 - (price_log + 3) / 6
            norm_price = max(0.0, min(1.0, norm_price))

        # Weighting
        score = (
            (norm_intel**task_profile.intel_weight)
            * (norm_speed**task_profile.speed_weight)
            * (norm_price**task_profile.price_weight)
        )

        return score

    def filter_candidates(
        self,
        models: List[MarketModel],
        min_intel: float = 0,
        max_intel: float = 100,
        min_speed: float = 0,
        max_speed: float = float("inf"),
        min_price: float = 0,
        max_price: float = float("inf"),
        min_context: int = 0,
        max_context: int = 2**31 - 1,
        local_only: bool = False,
        commercial_only: bool = False,
    ) -> List[MarketModel]:
        """Filter models based on hardware constraints, performance metrics and user preferences."""
        candidates = []
        available_mem = self.sys_profile.ram_gb
        if self.sys_profile.vram_gb:
            available_mem += self.sys_profile.vram_gb

        for m in models:
            # 1. Type Filtering
            if local_only and not m.local:
                continue
            if commercial_only and m.local:
                continue

            # 2. Performance/Price/Context Filtering
            if not (min_intel <= m.intelligence <= max_intel):
                continue
            if not (min_speed <= m.speed_tps <= max_speed):
                continue
            if not (min_price <= m.output_per_mtok <= max_price):
                continue
            if not (min_context <= m.context_window <= max_context):
                continue

            # 3. Hardware check for local models
            if m.local:
                # Extract params from ID (heuristic)
                import re

                match = re.search(r"(\d+(\.\d+)?)b", m.id.lower())
                params = float(match.group(1)) if match else 7.0

                # If it's already running (status="running"), we assume it fits
                if m.status != "running":
                    est_mem = estimate_footprint(
                        int(params), "Q4_K_M"
                    )  # Assume standard quant
                    if est_mem > available_mem * 0.9:  # Leave 10% buffer
                        continue

            candidates.append(m)
        return candidates

    def recommend(
        self,
        models: List[MarketModel],
        profile_name: str = "chat",
        limit: int = 5,
        **filters,
    ) -> List[Dict]:
        """Rank and return top recommendations."""
        task_profile = PROFILES.get(profile_name, PROFILES["chat"])
        candidates = self.filter_candidates(models, **filters)

        results = []
        for m in candidates:
            score = self.score_model(m, task_profile)
            results.append(
                {
                    "model": m,
                    "score": score * 100,  # Scale to 0-100 for display
                }
            )

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
