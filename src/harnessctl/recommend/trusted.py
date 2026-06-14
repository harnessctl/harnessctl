TRUSTED_ORGS = {
    # Labs & Original Authors
    "meta-llama",
    "mistralai",
    "google",
    "microsoft",
    "anthropic",
    "openai",
    "deepseek-ai",
    "qwen",
    "nousresearch",
    "nexusflow",
    "cohereforai",
    "gradientai",
    "nvidia",
    "apple",
    # Top Tier Community Quantizers (Reliable performance & metadata)
    "unsloth",
    "bartowski",
    "mradermacher",
    "maziyarpanahi",
    "thebloke",
    "lonestriker",
    "m-a-p",
    "lmstudio-community",
}


def is_trusted_author(model_id: str) -> bool:
    """Checks if the model author is in the trusted list."""
    if "/" not in model_id:
        return True  # Official library models or local relative paths

    author = model_id.split("/")[0].lower()
    return author in TRUSTED_ORGS
