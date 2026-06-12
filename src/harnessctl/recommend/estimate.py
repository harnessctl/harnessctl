from harnessctl.sysprobe.profile import SystemProfile

QUANT_BITS = {
    "Q2_K": 2.5,
    "Q3_K_S": 3.0,
    "Q3_K_M": 3.5,
    "Q4_0": 4.5,
    "Q4_K_S": 4.5,
    "Q4_K_M": 4.5,
    "Q5_K_S": 5.5,
    "Q5_K_M": 5.5,
    "Q6_K": 6.0,
    "Q8_0": 8.0,
    "F16": 16.0,
    "F32": 32.0,
}


def estimate_footprint(params_billion: int, quant: str) -> float:
    """Estimate memory footprint in GB for a given model size and quantization."""
    bits_per_param = QUANT_BITS.get(quant)
    if bits_per_param is None:
        raise ValueError(f"Unknown quantization: {quant}")

    # params_billion * 1e9 * bits_per_param / 8 / 1e9 = params_billion * bits_per_param / 8
    base_gb = params_billion * bits_per_param / 8
    overhead_factor = 1.2
    return base_gb * overhead_factor


def fits_in_memory(profile: SystemProfile, params_billion: int, quant: str) -> bool:
    """Check if a model fits in available RAM + VRAM."""
    estimated_gb = estimate_footprint(params_billion, quant)
    available_gb = profile.free_ram_gb
    if profile.vram_gb is not None:
        available_gb += profile.vram_gb
    return estimated_gb <= available_gb
