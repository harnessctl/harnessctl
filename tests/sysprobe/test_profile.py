import pytest
from unittest.mock import patch, MagicMock
from harnessctl.sysprobe.profile import detect_system


@pytest.fixture
def mock_psutil():
    with (
        patch("psutil.virtual_memory") as mock_mem,
        patch("psutil.cpu_count") as mock_cpu,
    ):
        mem_mock = MagicMock()
        mem_mock.total = 16 * (1024**3)
        mem_mock.available = 8 * (1024**3)
        mock_mem.return_value = mem_mock

        mock_cpu.return_value = 8

        yield mock_mem, mock_cpu


def test_detect_system_linux_basic(mock_psutil):
    with (
        patch("platform.system", return_value="Linux"),
        patch("platform.machine", return_value="x86_64"),
        patch("harnessctl.sysprobe.profile.pynvml", None),
        patch("subprocess.check_output", side_effect=FileNotFoundError),
    ):
        profile = detect_system()
        assert profile.os == "linux"
        assert profile.arch == "x86_64"
        assert profile.ram_gb == 16.0
        assert profile.free_ram_gb == 8.0
        assert profile.cpu_cores == 8
        assert profile.gpu_kind is None
        assert profile.vram_gb is None


def test_detect_system_darwin_metal(mock_psutil):
    with (
        patch("platform.system", return_value="Darwin"),
        patch("platform.machine", return_value="arm64"),
        patch("harnessctl.sysprobe.profile.pynvml", None),
        patch(
            "subprocess.check_output", return_value="Metal: Supported\nVRAM: 4096 MB"
        ),
    ):
        profile = detect_system()
        assert profile.os == "darwin"
        assert profile.arch == "arm64"
        assert profile.gpu_kind == "metal"
        assert profile.vram_gb == 4.0


def test_detect_system_nvidia_pynvml(mock_psutil):
    mock_pynvml = MagicMock()
    mock_pynvml.nvmlDeviceGetMemoryInfo.return_value.total = 8 * (1024**3)

    with (
        patch("platform.system", return_value="Linux"),
        patch("platform.machine", return_value="x86_64"),
        patch("harnessctl.sysprobe.profile.pynvml", mock_pynvml),
    ):
        profile = detect_system()
        assert profile.gpu_kind == "nvidia"
        assert profile.vram_gb == 8.0
        mock_pynvml.nvmlInit.assert_called_once()


def test_detect_system_nvidia_smi_fallback(mock_psutil):
    with (
        patch("platform.system", return_value="Linux"),
        patch("platform.machine", return_value="x86_64"),
        patch("harnessctl.sysprobe.profile.pynvml", None),
        patch("subprocess.check_output", return_value="12288\n"),
    ):
        profile = detect_system()
        assert profile.gpu_kind == "nvidia"
        assert profile.vram_gb == 12.0
