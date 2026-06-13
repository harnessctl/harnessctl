import pytest
import asyncio
from unittest.mock import patch, MagicMock
from harnessctl.discovery.base import DiscoveredModel, RuntimeProbe, run_probes
from harnessctl.discovery.ollama import OllamaProbe
from harnessctl.discovery.openai_compat import OpenAICompatProbe
from harnessctl.discovery.mlx import MLXProbe


class DummyProbe(RuntimeProbe):
    def __init__(self, models, delay=0):
        self._models = models
        self._delay = delay

    async def probe(self):
        await asyncio.sleep(self._delay)
        if self._models is None:
            raise ValueError("Probe failed")
        return self._models


@pytest.mark.asyncio
async def test_run_probes():
    p1 = DummyProbe([DiscoveredModel("test", "m1", "http://test")])
    p2 = DummyProbe([DiscoveredModel("test", "m2", "http://test")])
    res = await run_probes([p1, p2])
    assert len(res) == 2


@pytest.mark.asyncio
async def test_run_probes_timeout():
    p1 = DummyProbe([DiscoveredModel("test", "m1", "http://test")])
    p2 = DummyProbe([DiscoveredModel("test", "m2", "http://test")], delay=3)
    # timeout is 2 by default
    res = await run_probes([p1, p2], timeout=0.1)
    assert len(res) == 1
    assert res[0].id == "m1"


@pytest.mark.asyncio
async def test_run_probes_exception():
    p1 = DummyProbe(None)
    res = await run_probes([p1])
    assert len(res) == 0


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_ollama_probe(mock_get):
    mock_get.return_value = MagicMock(json=lambda: {"models": [{"name": "llama3:8b"}]})
    p = OllamaProbe()
    res = await p.probe()
    assert len(res) == 1
    assert res[0].id == "llama3:8b"


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
async def test_openai_compat_probe(mock_get):
    mock_get.return_value = MagicMock(
        status_code=200, json=lambda: {"data": [{"id": "gpt-4"}]}
    )
    p = OpenAICompatProbe(runtime="lmstudio", endpoint="http://localhost:1234/v1")
    res = await p.probe()
    assert len(res) == 1
    assert res[0].id == "gpt-4"
    assert res[0].runtime == "lmstudio"


@pytest.mark.asyncio
@patch("platform.system")
async def test_mlx_probe_not_mac(mock_sys):
    mock_sys.return_value = "Linux"
    p = MLXProbe()
    res = await p.probe()
    assert len(res) == 0
