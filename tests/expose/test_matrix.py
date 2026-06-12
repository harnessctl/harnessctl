import pytest
from harnessctl.expose.matrix import get_compatible_engines, resolve_best_format
from harnessctl.sysprobe.profile import SystemProfile


@pytest.fixture
def linux_profile():
    return SystemProfile(
        ram_gb=16.0,
        free_ram_gb=8.0,
        cpu_cores=8,
        vram_gb=None,
        gpu_kind=None,
        os="linux",
        arch="x86_64",
    )


@pytest.fixture
def mac_profile():
    return SystemProfile(
        ram_gb=16.0,
        free_ram_gb=8.0,
        cpu_cores=8,
        vram_gb=None,
        gpu_kind="metal",
        os="darwin",
        arch="arm64",
    )


def test_get_compatible_engines_gguf(linux_profile):
    engines = get_compatible_engines("gguf", linux_profile)
    assert "llama.cpp" in engines
    assert "ollama" in engines


def test_get_compatible_engines_mlx_linux(linux_profile):
    engines = get_compatible_engines("mlx", linux_profile)
    assert engines == []


def test_get_compatible_engines_mlx_mac(mac_profile):
    engines = get_compatible_engines("mlx", mac_profile)
    assert "mlx" in engines


def test_resolve_best_format_mac(mac_profile):
    fmt, engines = resolve_best_format(["gguf", "mlx"], mac_profile)
    assert fmt == "mlx"
    assert engines == ["mlx"]


def test_resolve_best_format_linux(linux_profile):
    fmt, engines = resolve_best_format(["gguf", "mlx"], linux_profile)
    assert fmt == "gguf"
    assert "llama.cpp" in engines
