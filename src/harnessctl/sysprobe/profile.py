import platform
import subprocess
import re
import psutil
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

try:
    import pynvml
except ImportError:
    pynvml = None


@dataclass
class SystemProfile:
    ram_gb: float
    free_ram_gb: float
    cpu_cores: int
    vram_gb: Optional[float]
    gpu_kind: Optional[str]  # "nvidia", "metal", None
    os: str  # "linux", "darwin", "windows"
    arch: str  # "x86_64", "arm64"


def _detect_nvidia_vram() -> Optional[float]:
    """Detect NVIDIA VRAM in GB using pynvml."""
    if not pynvml:
        # Fallback to nvidia-smi if pynvml is not installed
        try:
            output = subprocess.check_output(
                [
                    "nvidia-smi",
                    "--query-gpu=memory.total",
                    "--format=csv,noheader,nounits",
                ],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            if output.strip():
                vram_mb = float(output.strip().split("\n")[0])
                return vram_mb / 1024
        except (subprocess.SubprocessError, FileNotFoundError, ValueError):
            return None
        return None

    try:
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        pynvml.nvmlShutdown()
        return info.total / (1024**3)
    except Exception:
        return None


def _detect_metal_vram() -> Optional[float]:
    """Detect Apple Metal VRAM in GB using system_profiler."""
    if platform.system() != "Darwin":
        return None

    try:
        output = subprocess.check_output(
            ["system_profiler", "SPDisplaysDataType"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        # Extract VRAM if possible
        match = re.search(r"VRAM.*?(\d+)\s*MB", output)
        if match:
            return int(match.group(1)) / 1024

        # Newer Macs might not show VRAM explicitly as it's Unified Memory
        if "Metal" in output:
            return None  # Will fall back to RAM-only estimate for Unified Memory
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return None


def _detect_linux_drm_vram() -> Optional[float]:
    """Detect VRAM in GB for AMD/Intel via DRM sysfs (Linux only)."""
    if platform.system() != "Linux":
        return None

    try:
        vram_values = []
        # Standard DRM path for memory info (covers AMD and Intel Arc)
        for p in Path("/sys/class/drm/").glob("card*/device/mem_info_vram_total"):
            try:
                val = int(p.read_text().strip())
                if val > 0:
                    vram_values.append(val)
            except (ValueError, OSError):
                continue

        if vram_values:
            return max(vram_values) / (1024**3)
    except Exception:
        pass

    return None


def detect_system() -> SystemProfile:
    """Detect system hardware capabilities."""
    os_name = platform.system().lower()
    arch = platform.machine()

    # RAM detection
    mem = psutil.virtual_memory()
    ram_gb = mem.total / (1024**3)
    free_ram_gb = mem.available / (1024**3)

    # CPU cores
    cpu_cores = psutil.cpu_count(logical=False) or psutil.cpu_count() or 1

    # GPU detection (Strategy: Specialized -> Generic -> Platform-specific)
    vram_gb = _detect_nvidia_vram()
    gpu_kind = "nvidia" if vram_gb is not None else None

    # Try Generic Linux DRM (covers AMD and Intel Arc)
    if vram_gb is None and os_name == "linux":
        vram_gb = _detect_linux_drm_vram()
        if vram_gb is not None:
            gpu_kind = "gpu"
            try:
                # Heuristic vendor detection
                for p in Path("/sys/class/drm/").glob("card*/device/vendor"):
                    vendor = p.read_text().strip().lower()
                    if "0x1002" in vendor or "amd" in vendor:
                        gpu_kind = "amd"
                        break
                    if "0x8086" in vendor or "intel" in vendor:
                        gpu_kind = "intel"
                        break
            except Exception:
                pass

    # Try Apple Metal
    if vram_gb is None and os_name == "darwin":
        vram_gb = _detect_metal_vram()
        if vram_gb is not None or "arm" in arch.lower():
            gpu_kind = "metal"

    return SystemProfile(
        ram_gb=ram_gb,
        free_ram_gb=free_ram_gb,
        cpu_cores=cpu_cores,
        vram_gb=vram_gb,
        gpu_kind=gpu_kind,
        os=os_name,
        arch=arch,
    )
