from typing import List
from harnessctl.pricing.catalog import MarketModel
from harnessctl.spec.warnings import WarningCollector
from harnessctl.pricing.market import get_intelligence_score, get_speed_score

GOOGLE_MODELS_URL = "https://generativelanguage.googleapis.com/v1beta/models"


async def fetch_google_market(
    warnings: WarningCollector, force_refresh: bool = False
) -> List[MarketModel]:
    """Fetch models from Google Gemini API."""
    from harnessctl.providers.manager import SecretsManager
    from harnessctl.pricing.common import fetch_prices_generic

    secrets = SecretsManager()
    key = secrets.get_token("google")

    if not key:
        warnings.add(
            field="google_market",
            reason="API key missing. Discovery skipped.",
        )
        return []

    data = await fetch_prices_generic(
        "google_market",
        f"{GOOGLE_MODELS_URL}?key={key}",
        warnings,
        force_refresh=force_refresh,
    )

    if not data or "models" not in data:
        return []

    market_models = []
    for item in data["models"]:
        # Format: "models/gemini-1.5-pro"
        full_id = item.get("name", "")
        if not full_id.startswith("models/"):
            continue

        model_id = full_id.replace("models/", "")

        # Filter for models that actually support generation
        if "generateContent" not in item.get("supportedGenerationMethods", []):
            continue

        intel, intel_src = get_intelligence_score({"id": model_id})

        market_models.append(
            MarketModel(
                id=f"google/{model_id}",
                name=item.get("displayName", model_id),
                provider="google",
                input_per_mtok=0.0,  # Pricing varies by tier, complex to map statically here
                output_per_mtok=0.0,
                context_window=item.get("inputTokenLimit", 0),
                intelligence=intel,
                intelligence_source=intel_src,
                speed_tps=get_speed_score({"id": model_id}),
                local=False,
                status="available",
            )
        )
    return market_models
