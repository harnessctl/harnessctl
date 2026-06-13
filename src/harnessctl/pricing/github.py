from typing import List
from harnessctl.pricing.catalog import MarketModel
from harnessctl.spec.warnings import WarningCollector
from harnessctl.pricing.market import get_intelligence_score, get_speed_score

GITHUB_MODELS_URL = "https://models.inference.ai.azure.com/models"
GITHUB_COPILOT_URL = "https://api.githubcopilot.com/models"


async def fetch_github_models_market(
    warnings: WarningCollector, force_refresh: bool = False
) -> List[MarketModel]:
    """Fetch models from GitHub Models (Marketplace)."""
    from harnessctl.providers.manager import SecretsManager
    from harnessctl.pricing.common import fetch_prices_generic

    secrets = SecretsManager()
    token = secrets.get_token("github")

    if not token:
        warnings.add(
            field="github_models",
            reason="Token missing. Discovery skipped.",
        )
        return []

    data = await fetch_prices_generic(
        "github_models",
        GITHUB_MODELS_URL,
        warnings,
        force_refresh=force_refresh,
        headers={"Authorization": f"Bearer {token}"},
    )

    if not data or not isinstance(data, list):
        return []

    market_models = []
    for item in data:
        model_id = item.get("name")
        if not model_id:
            continue

        intel, intel_src = get_intelligence_score({"id": model_id})

        market_models.append(
            MarketModel(
                id=f"github/{model_id}",
                name=model_id,
                provider="github-models",
                input_per_mtok=0.0,  # Typically free/included in tier
                output_per_mtok=0.0,
                context_window=item.get("max_tokens", 0),
                intelligence=intel,
                intelligence_source=intel_src,
                speed_tps=get_speed_score({"id": model_id}),
                local=False,
                status="available",
            )
        )
    return market_models


async def fetch_github_copilot_market(
    warnings: WarningCollector, force_refresh: bool = False
) -> List[MarketModel]:
    """Fetch models from GitHub Copilot Chat API."""
    from harnessctl.providers.manager import SecretsManager
    from harnessctl.pricing.common import fetch_prices_generic

    secrets = SecretsManager()
    token = secrets.get_token("github")

    if not token:
        warnings.add(
            field="github_copilot",
            reason="Token missing. Discovery skipped.",
        )
        return []

    data = await fetch_prices_generic(
        "github_copilot",
        GITHUB_COPILOT_URL,
        warnings,
        force_refresh=force_refresh,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )

    if not data or "data" not in data:
        return []

    market_models = []
    for item in data["data"]:
        model_id = item.get("id")
        if not model_id:
            continue

        intel, intel_src = get_intelligence_score({"id": model_id})

        market_models.append(
            MarketModel(
                id=f"github-copilot/{model_id}",
                name=item.get("name", model_id),
                provider="github-copilot",
                input_per_mtok=0.0,  # Included in subscription
                output_per_mtok=0.0,
                context_window=item.get(
                    "max_tokens", 0
                ),  # Or similar metadata if present
                intelligence=intel,
                intelligence_source=intel_src,
                speed_tps=get_speed_score({"id": model_id}),
                local=False,
                status="available",
            )
        )
    return market_models
