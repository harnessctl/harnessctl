import httpx
import psutil
import platform
from enum import Enum
from typing import List, Optional
from dataclasses import dataclass


class ServiceStatus(Enum):
    ACTIVE = "Active"
    STARTED = "Started"
    INACTIVE = "Inactive"


@dataclass
class ServiceInfo:
    name: str
    status: ServiceStatus
    endpoint: Optional[str] = None


async def check_service_status(
    name: str, url: str, process_names: List[str]
) -> ServiceStatus:
    """Check if a service is active via API or started via process."""
    # 1. Check API
    async with httpx.AsyncClient(timeout=2.0) as client:
        try:
            response = await client.get(url)
            # Accept most success or redirect codes
            if response.status_code < 500:
                return ServiceStatus.ACTIVE
        except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError):
            pass

    # 2. Check Process
    for proc in psutil.process_iter(["name", "cmdline"]):
        try:
            # Check name
            if proc.info["name"] and any(
                pn.lower() in proc.info["name"].lower() for pn in process_names
            ):
                return ServiceStatus.STARTED

            # Check cmdline for python modules
            cmdline = proc.info["cmdline"]
            if cmdline:
                cmd_str = " ".join(cmdline).lower()
                if any(pn.lower() in cmd_str for pn in process_names):
                    return ServiceStatus.STARTED
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    return ServiceStatus.INACTIVE


async def get_all_services_status() -> List[ServiceInfo]:
    """Get status for all supported local inference services."""
    system = platform.system()

    # Common services
    service_configs = [
        ("Ollama", "http://localhost:11434/api/tags", ["ollama"]),
        ("LM Studio", "http://localhost:1234/v1/models", ["lm studio", "lm-studio"]),
        ("Llama.cpp", "http://localhost:8080/health", ["llama-server", "llama.cpp"]),
    ]

    results = []
    for name, url, procs in service_configs:
        status = await check_service_status(name, url, procs)
        results.append(ServiceInfo(name=name, status=status, endpoint=url))

    # Mac specific: MLX
    if system == "Darwin":
        status = await check_service_status(
            "MLX", "http://localhost:8080/v1/models", ["mlx_lm.server", "mlx-lm"]
        )
        results.append(
            ServiceInfo(
                name="MLX", status=status, endpoint="http://localhost:8080/v1/models"
            )
        )

    return results
