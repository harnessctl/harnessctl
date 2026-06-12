from typing import List, Tuple
from harnessctl.sysprobe.profile import SystemProfile

FORMAT_ENGINE_MATRIX = {
    "gguf": ["llama.cpp", "lmstudio", "ollama"],
    "mlx": ["mlx"],
    "safetensors": [],  # Requires conversion
}


def get_compatible_engines(format: str, profile: SystemProfile) -> List[str]:
    """Get list of compatible engines for a given format and system profile."""
    engines = FORMAT_ENGINE_MATRIX.get(format.lower(), [])

    # OS Gates
    if "mlx" in engines and profile.os != "darwin":
        return []

    return engines


def resolve_best_format(
    available_formats: List[str], profile: SystemProfile
) -> Tuple[str, List[str]]:
    """Pick the best format based on availability and system compatibility."""
    # Priority: MLX on macOS, GGUF everywhere else
    if profile.os == "darwin" and "mlx" in available_formats:
        return "mlx", ["mlx"]

    if "gguf" in available_formats:
        return "gguf", get_compatible_engines("gguf", profile)

    if available_formats:
        # Fallback to first available but maybe empty engines
        return available_formats[0], get_compatible_engines(
            available_formats[0], profile
        )

    return "unknown", []
