import pytest
import os
from unittest.mock import patch

from harnessctl.pricing.cache import (
    read_cache,
    write_cache,
    read_stale_cache,
    get_cache_path,
)
from harnessctl.pricing.litellm import fetch_litellm_prices
from harnessctl.pricing.openrouter import fetch_openrouter_prices
from harnessctl.pricing.catalog import merge_market_data, MarketModel
from harnessctl.discovery.base import DiscoveredModel
from harnessctl.spec.warnings import WarningCollector


def test_cache_logic(tmp_path):
    with patch("harnessctl.pricing.cache.CACHE_DIR", tmp_path):
        data = {"model_a": {"price": 1}}
        write_cache("test", data)

        # Valid cache
        assert read_cache("test", ttl_hours=24) == data
        assert read_stale_cache("test") == data

        # Expired cache
        with patch(
            "time.time",
            return_value=os.path.getmtime(get_cache_path("test")) + 25 * 3600,
        ):
            assert read_cache("test", ttl_hours=24) is None
            # Stale ignores TTL
            assert read_stale_cache("test") == data


@pytest.mark.asyncio
@patch("harnessctl.pricing.common.read_cache")
@patch("httpx.AsyncClient.get")
async def test_litellm_fetch(mock_get, mock_read_cache):
    # simulate no cache
    mock_read_cache.return_value = None

    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "gpt-4": {
                    "input_cost_per_token": 0.03,
                    "output_cost_per_token": 0.06,
                    "max_tokens": 8192,
                }
            }

    mock_get.return_value = MockResponse()

    with patch("harnessctl.pricing.litellm.write_cache"):
        warnings = WarningCollector()
        res = await fetch_litellm_prices(warnings)

        assert "gpt-4" in res
        assert res["gpt-4"]["input_per_mtok"] == 30000.0
        assert res["gpt-4"]["output_per_mtok"] == 60000.0
        assert res["gpt-4"]["context_window"] == 8192


@pytest.mark.asyncio
@patch("harnessctl.pricing.common.read_cache")
@patch("httpx.AsyncClient.get")
async def test_openrouter_fetch(mock_get, mock_read_cache):
    mock_read_cache.return_value = None

    class MockResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "data": [
                    {
                        "id": "openai/gpt-4",
                        "pricing": {"prompt": "0.00003", "completion": "0.00006"},
                        "context_length": 8192,
                    }
                ]
            }

    mock_get.return_value = MockResponse()

    with patch("harnessctl.pricing.openrouter.write_cache"):
        warnings = WarningCollector()
        res = await fetch_openrouter_prices(warnings)

        assert "openai/gpt-4" in res
        assert res["openai/gpt-4"]["input_per_mtok"] == 30.0  # 0.00003 * 1m
        assert res["openai/gpt-4"]["output_per_mtok"] == 60.0


def test_market_merge():
    discovered = [
        DiscoveredModel(
            runtime="ollama", id="llama3:8b", endpoint="http://localhost", local=True
        )
    ]
    commercial = [
        MarketModel(
            id="openai/gpt-4",
            name="GPT-4",
            provider="openrouter",
            input_per_mtok=10.0,
            output_per_mtok=20.0,
            context_window=8000,
            intelligence=90.0,
            speed_tps=20.0,
            local=False,
            status="available",
        ),
        MarketModel(
            id="anthropic/claude-3",
            name="Claude 3",
            provider="openrouter",
            input_per_mtok=15.0,
            output_per_mtok=30.0,
            context_window=200000,
            intelligence=95.0,
            speed_tps=30.0,
            local=False,
            status="available",
        ),
    ]

    catalog = merge_market_data(discovered, commercial)

    # 3 models total
    assert len(catalog) == 3

    # Verify local model estimation
    local_model = next(m for m in catalog if m.id == "llama3:8b")
    assert local_model.local is True
    assert local_model.intelligence == 50.0  # 8b heuristic
    assert local_model.speed_tps == 80.0  # 8b heuristic

    # Verify commercial models preserved
    assert any(m.id == "openai/gpt-4" for m in catalog)
    assert any(m.id == "anthropic/claude-3" for m in catalog)
