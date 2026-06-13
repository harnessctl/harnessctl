import asyncio
from harnessctl.discovery.base import run_probes
from harnessctl.discovery.ollama import OllamaProbe
from harnessctl.discovery.mlx import MLXProbe
from harnessctl.discovery.openai_compat import OpenAICompatProbe
from harnessctl.discovery.opencode import OpencodeProbe


def discover_all():
    """Sync wrapper for run_probes with default probes."""
    probes = [
        OllamaProbe(),
        MLXProbe(),
        OpenAICompatProbe(runtime="lmstudio", endpoint="http://localhost:1234/v1"),
        OpencodeProbe(),
    ]

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(run_probes(probes))
    finally:
        loop.close()
