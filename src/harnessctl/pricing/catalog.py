from dataclasses import dataclass
from typing import List, Dict, Any
from harnessctl.discovery.base import DiscoveredModel


@dataclass
class PricedModel:
    id: str
    provider: str
    input_per_mtok: float
    output_per_mtok: float
    context_window: int
    local: bool
    status: str


def merge_catalog(
    discovered: List[DiscoveredModel],
    litellm_prices: Dict[str, Any],
    openrouter_prices: Dict[str, Any],
) -> List[PricedModel]:
    catalog: Dict[str, PricedModel] = {}

    # 1. Local models (from discovery)
    for model in discovered:
        # Avoid overriding if already there, or merge? Let's just add
        catalog[model.id] = PricedModel(
            id=model.id,
            provider=model.runtime,
            input_per_mtok=0.0,
            output_per_mtok=0.0,
            context_window=0,  # We don't know context window for local easily
            local=True,
            status="running",
        )

    # 2. Cloud models (OpenRouter)
    for model_id, info in openrouter_prices.items():
        if model_id not in catalog:
            catalog[model_id] = PricedModel(
                id=model_id,
                provider=info["provider"],
                input_per_mtok=info["input_per_mtok"],
                output_per_mtok=info["output_per_mtok"],
                context_window=info["context_window"],
                local=False,
                status="available",
            )

    # 3. Cloud models (LiteLLM)
    for model_id, info in litellm_prices.items():
        if model_id not in catalog:
            catalog[model_id] = PricedModel(
                id=model_id,
                provider=info["provider"],
                input_per_mtok=info["input_per_mtok"],
                output_per_mtok=info["output_per_mtok"],
                context_window=info["context_window"],
                local=False,
                status="available",
            )

    # Sort cheapest first
    result = list(catalog.values())
    result.sort(
        key=lambda m: (m.input_per_mtok, m.output_per_mtok, -m.context_window, m.id)
    )
    return result
