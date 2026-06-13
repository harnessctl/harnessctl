import asyncio
from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredModel:
    runtime: str
    id: str
    endpoint: str
    local: bool = True
    metadata: dict = None


class RuntimeProbe(ABC):
    @abstractmethod
    async def probe(self) -> List[DiscoveredModel]:
        """Probe the runtime and return a list of discovered models."""
        pass


async def run_probes(
    probes: List[RuntimeProbe], timeout: float = 5.0
) -> List[DiscoveredModel]:
    """Run multiple probes concurrently, with a timeout for each."""

    async def run_with_timeout(probe: RuntimeProbe) -> List[DiscoveredModel]:
        try:
            return await asyncio.wait_for(probe.probe(), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(
                f"Probe {probe.__class__.__name__} timed out after {timeout}s"
            )
            return []
        except Exception as e:
            logger.warning(f"Probe {probe.__class__.__name__} failed: {e}")
            return []

    results = await asyncio.gather(*(run_with_timeout(p) for p in probes))

    flattened = []
    for r in results:
        flattened.extend(r)
    return flattened
