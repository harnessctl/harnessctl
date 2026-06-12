from typing import List, Optional
from dataclasses import dataclass
from huggingface_hub import HfApi
from harnessctl.recommend.estimate import estimate_footprint, fits_in_memory
from harnessctl.sysprobe.profile import SystemProfile


@dataclass
class RankedModel:
    repo_id: str
    quant: str
    params_billion: float
    estimated_memory_gb: float
    backend: str  # e.g., "llama.cpp", "mlx"
    score: float
    context_window: int = 4096  # default
    size_bytes: Optional[int] = None


def search_candidates(
    profile: SystemProfile,
    tags: List[str] = ["gguf", "coding", "instruct"],
    limit: int = 10,
) -> List[RankedModel]:
    """Search and rank HF models based on system fit and capability."""
    api = HfApi()

    # Filter models by tags
    models = api.list_models(
        tags=tags,
        sort="downloads",
        direction=-1,
        limit=limit * 2,  # Fetch more to allow for filtering
    )

    candidates = []
    for model in models:
        try:
            # Check for GGUF files
            files = api.list_repo_files(model.modelId)
            gguf_files = [f for f in files if f.endswith(".gguf")]
            if not gguf_files:
                continue

            # Extract quant from filenames
            available_quants = []
            for f in gguf_files:
                if "Q" in f or "F16" in f or "F32" in f:
                    for q in [
                        "Q2_K",
                        "Q3_K_S",
                        "Q3_K_M",
                        "Q4_0",
                        "Q4_K_S",
                        "Q4_K_M",
                        "Q5_K_S",
                        "Q5_K_M",
                        "Q6_K",
                        "Q8_0",
                        "F16",
                        "F32",
                    ]:
                        if q in f:
                            available_quants.append((q, f))
                            break

            if not available_quants:
                continue

            # Estimate params from model name
            params_billion = 7.0  # default
            model_id_lower = model.modelId.lower()
            import re

            m = re.search(r"(\d+(\.\d+)?)b", model_id_lower)
            if m:
                params_billion = float(m.group(1))

            # Evaluate each quantization for fit
            for quant, filename in available_quants:
                if fits_in_memory(profile, int(params_billion), quant):
                    est_gb = estimate_footprint(int(params_billion), quant)

                    # Scoring: prefer larger models and higher quants that still fit
                    # Score = params_billion * bits_per_param
                    from harnessctl.recommend.estimate import QUANT_BITS

                    score = params_billion * QUANT_BITS.get(quant, 4.0)

                    # Bonus for coding if requested
                    if "coding" in tags and "code" in model_id_lower:
                        score *= 1.2

                    candidates.append(
                        RankedModel(
                            repo_id=model.modelId,
                            quant=quant,
                            params_billion=params_billion,
                            estimated_memory_gb=est_gb,
                            backend="mlx"
                            if profile.gpu_kind == "metal" and "mlx" in model_id_lower
                            else "llama.cpp",
                            score=score,
                            size_bytes=None,  # We'd need to fetch file info for this
                        )
                    )
        except Exception:
            # Skip models that fail to list files or other issues
            continue

    # Sort by score descending and return top matches
    candidates.sort(key=lambda x: x.score, reverse=True)

    # De-duplicate by repo_id, keeping the best quant for each
    seen_repos = {}
    unique_candidates = []
    for c in candidates:
        if c.repo_id not in seen_repos:
            seen_repos[c.repo_id] = True
            unique_candidates.append(c)

    return unique_candidates[:limit]
