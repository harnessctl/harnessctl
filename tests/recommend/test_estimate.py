import pytest
from harnessctl.recommend.estimate import estimate_footprint, fits_in_memory
from harnessctl.sysprobe.profile import SystemProfile


def test_estimate_footprint():
    # 7B Q4_K_M: 7 * 4.5 / 8 * 1.2 ≈ 4.725
    assert abs(estimate_footprint(7, "Q4_K_M") - 4.725) < 0.001
    # 13B F16: 13 * 16 / 8 * 1.2 = 31.2
    assert abs(estimate_footprint(13, "F16") - 31.2) < 0.001
    # unknown quant raises ValueError
    with pytest.raises(ValueError):
        estimate_footprint(7, "unknown")


def test_fits_in_memory():
    profile = SystemProfile(
        ram_gb=16.0,
        free_ram_gb=8.0,
        cpu_cores=8,
        vram_gb=4.0,
        gpu_kind="nvidia",
        os="linux",
        arch="x86_64",
    )
    # 7B Q4_K_M ≈ 4.725 GB, free RAM 8 + VRAM 4 = 12 GB → fits
    assert fits_in_memory(profile, 7, "Q4_K_M") is True
    # 70B Q4_K_M ≈ 47.25 GB, does not fit
    assert fits_in_memory(profile, 70, "Q4_K_M") is False


def test_fits_in_memory_no_vram():
    profile = SystemProfile(
        ram_gb=16.0,
        free_ram_gb=8.0,
        cpu_cores=8,
        vram_gb=None,
        gpu_kind=None,
        os="linux",
        arch="x86_64",
    )
    # 7B Q4_K_M ≈ 4.725 GB, free RAM 8 GB → fits
    assert fits_in_memory(profile, 7, "Q4_K_M") is True
    # 13B F16 ≈ 31.2 GB, does not fit
    assert fits_in_memory(profile, 13, "F16") is False
