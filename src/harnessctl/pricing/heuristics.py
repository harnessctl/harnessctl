from typing import Tuple


def get_intel_heuristic(model_id: str) -> float:
    """Estimate intelligence score (0-100) based on model name/ID."""
    name = model_id.lower()

    # Tier 1: SOTA classes
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
            "gemini-1.5-pro",
            "opus",
            "abacus",
        ]
    ):
        return 95.0

    # Tier 2: Strong classes
    if any(k in name for k in ["gpt-4", "llama-3.1-405b", "smaug", "sonnet"]):
        return 90.0

    # Tier 3: Mid-tier
    if any(
        k in name for k in ["llama-3.1-70b", "qwen2.5-72b", "deepseek-v2.5", "phi-4"]
    ):
        return 80.0

    # Tier 4: Small models
    if any(
        k in name for k in ["haiku", "flash", "mini", "8b", "llama-3.1-8b", "phi-3"]
    ):
        return 55.0

    # Tier 5: Specialty
    if any(k in name for k in ["coder", "qwen", "gemma"]):
        return 65.0

    return 40.0


def get_speed_heuristic(model_id: str) -> float:
    """Estimate speed (TPS) based on model name/ID."""
    name = model_id.lower()

    if any(
        k in name for k in ["mini", "flash", "haiku", "8b", "phi", "nano", "banana"]
    ):
        return 150.0
    if any(k in name for k in ["sonnet", "4o", "70b", "gemini-pro"]):
        return 70.0
    if any(k in name for k in ["opus", "o1", "405b", "fable"]):
        return 15.0

    return 40.0


def get_pricing_heuristic(model_id: str) -> Tuple[float, float]:
    """Estimate pricing (input_per_mtok, output_per_mtok) based on model name/ID."""
    name = model_id.lower()

    # Tier 1: Free / Tiny
    if any(k in name for k in ["nano", "free", "trial", "banana"]):
        return 0.0, 0.0

    # Tier 2: Flash / Cheap
    if any(k in name for k in ["-mini", "flash", "haiku", "8b", "phi", "gemma"]):
        return 0.1, 0.4

    # Tier 3: Large / flagship
    if any(k in name for k in ["opus", "o1", "405b", "fable"]):
        return 15.0, 60.0

    # Tier 4: Mid-range (common for 4o, sonnet, 70b)
    if any(k in name for k in ["sonnet", "4o", "70b", "pro"]):
        return 3.0, 9.0

    return 1.0, 3.0
