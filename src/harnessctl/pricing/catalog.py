import re
from dataclasses import dataclass
from typing import List, Dict
from harnessctl.pricing.heuristics import get_intel_heuristic, get_speed_heuristic
from harnessctl.discovery.base import DiscoveredModel


@dataclass
class MarketModel:
    id: str
    name: str
    provider: str
    input_per_mtok: float
    output_per_mtok: float
    context_window: int
    intelligence: float  # 0-100
    intelligence_source: str  # "benchmark", "elo", "heuristic"
    speed_tps: float  # Tokens per second
    local: bool
    status: str


def estimate_local_metrics(model_id: str):
    """Estimate intel and speed for local models."""
    # Priority 1: Name-based heuristics (covers cloud models discovered via probes)
    intel = get_intel_heuristic(model_id)
    speed = get_speed_heuristic(model_id)

    # If it's a generic or unknown name (stays at 40), try param-based extraction for locals
    if intel == 40.0:
        model_id_lower = model_id.lower()
        # Extract params (e.g., 7b, 70b, 1.5b, 4-31b, 2.5-coder:14b)
        m = re.search(r"(\d+(\.\d+)?)b", model_id_lower)
        params = float(m.group(1)) if m else 7.0

        # Intelligence heuristic
        if params >= 70:
            intel = 80.0
        elif params >= 30:
            intel = 72.0
        elif params >= 13:
            intel = 65.0
        elif params >= 7:
            intel = 55.0

        # Speed heuristic (inverse of params)
        if params <= 3:
            speed = 150.0
        elif params <= 8:
            speed = 80.0
        elif params <= 14:
            speed = 45.0
        elif params <= 32:
            speed = 25.0
        else:
            speed = 8.0

        # Reasoning and Model Family Bonuses
        if "r1" in model_id_lower or "reasoning" in model_id_lower:
            intel += 10.0
        if any(k in model_id_lower for k in ["coder", "qwen", "gemma"]):
            intel += 5.0
        if "moe" in model_id_lower:
            intel += 3.0

    return min(98.0, intel), speed


def merge_market_data(
    discovered: List[DiscoveredModel],
    commercial_models: List[MarketModel],
) -> List[MarketModel]:
    """Combine local discovered models and commercial models into a single list."""
    catalog: Dict[str, MarketModel] = {}

    # 1. Commercial models (already processed by market aggregator)
    for model in commercial_models:
        catalog[model.id] = model

    # 2. Discovered models (Ollama, Opencode, etc.)
    for model in discovered:
        # If it's already in catalog, we might want to override some fields
        # but for now, let's just add it if missing or if it's local.
        if model.id in catalog and not model.local:
            continue

        intel, speed = estimate_local_metrics(model.id)

        catalog[model.id] = MarketModel(
            id=model.id,
            name=model.id,
            provider=model.metadata.get("provider", model.runtime)
            if model.metadata
            else model.runtime,
            input_per_mtok=0.0,
            output_per_mtok=0.0,
            context_window=128000 if not model.local else 32768,
            intelligence=intel,
            intelligence_source="heuristic",
            speed_tps=speed,
            local=model.local,
            status="running" if model.local else "available",
        )

    return list(catalog.values())
