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
    model_id_lower = model_id.lower()

    # Extract params (e.g., 7b, 70b, 1.5b, 4-31b, 2.5-coder:14b)
    # Match patterns like 7b, 1.5b, 31b
    m = re.search(r"(\d+(\.\d+)?)b", model_id_lower)
    params = float(m.group(1)) if m else 7.0

    # Intelligence heuristic
    if params >= 70:
        intel = 80.0
    elif params >= 30:
        intel = 72.0  # Slight bump for 30b class
    elif params >= 13:
        intel = 65.0
    elif params >= 7:
        intel = 55.0
    else:
        intel = 40.0

    # Reasoning and Model Family Bonuses
    if "r1" in model_id_lower or "reasoning" in model_id_lower:
        intel += 10.0
    if (
        "coder" in model_id_lower
        or "qwen" in model_id_lower
        or "gemma" in model_id_lower
    ):
        intel += 5.0
    if "moe" in model_id_lower:
        intel += 3.0

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
