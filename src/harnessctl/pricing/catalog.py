import re
from dataclasses import dataclass
from typing import List, Dict
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
    speed_tps: float  # Tokens per second
    local: bool
    status: str


def estimate_local_metrics(model_id: str):
    """Estimate intel and speed for local models."""
    intel = 40.0
    speed = 30.0

    # Extract params (e.g., 7b, 70b, 1.5b)
    m = re.search(r"(\d+(\.\d+)?)b", model_id.lower())
    params = float(m.group(1)) if m else 7.0

    # Intelligence heuristic
    if params >= 70:
        intel = 80.0
    elif params >= 30:
        intel = 70.0
    elif params >= 13:
        intel = 60.0
    elif params >= 7:
        intel = 50.0
    else:
        intel = 30.0

    if "r1" in model_id.lower() or "reasoning" in model_id.lower():
        intel += 10.0  # Reasoning bonus

    # Speed heuristic (inverse of params)
    if params <= 3:
        speed = 150.0
    elif params <= 8:
        speed = 80.0
    elif params <= 14:
        speed = 40.0
    elif params <= 32:
        speed = 20.0
    else:
        speed = 5.0

    return min(100.0, intel), speed


def merge_market_data(
    discovered: List[DiscoveredModel],
    commercial_models: List[MarketModel],
) -> List[MarketModel]:
    """Combine local discovered models and commercial models into a single list."""
    catalog: Dict[str, MarketModel] = {}

    # 1. Commercial models (already processed by market aggregator)
    for model in commercial_models:
        catalog[model.id] = model

    # 2. Local models (from discovery)
    for model in discovered:
        intel, speed = estimate_local_metrics(model.id)

        catalog[model.id] = MarketModel(
            id=model.id,
            name=model.id,
            provider=model.runtime,
            input_per_mtok=0.0,
            output_per_mtok=0.0,
            context_window=32768,  # Default for most modern locals
            intelligence=intel,
            speed_tps=speed,
            local=True,
            status="running",
        )

    return list(catalog.values())
