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
from harnessctl.pricing.catalog import merge_catalog
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


def test_catalog_merge():
    discovered = [
        DiscoveredModel(
            runtime="ollama", id="llama3:8b", endpoint="http://localhost", local=True
        )
    ]
    litellm = {
        "gpt-4": {
            "input_per_mtok": 30.0,
            "output_per_mtok": 60.0,
            "context_window": 8000,
            "provider": "litellm",
        }
    }
    openrouter = {
        "openai/gpt-4": {
            "input_per_mtok": 10.0,
            "output_per_mtok": 20.0,
            "context_window": 8000,
            "provider": "openrouter",
        },
        "gpt-4": {
            "input_per_mtok": 20.0,
            "output_per_mtok": 40.0,
            "context_window": 8000,
            "provider": "openrouter",
        },
    }

    catalog = merge_catalog(discovered, litellm, openrouter)

    # 3 models total (gpt-4 is in both, so it deduplicates)
    assert len(catalog) == 3

    # Check sorting
    assert catalog[0].id == "llama3:8b"
    assert catalog[0].input_per_mtok == 0.0
    assert catalog[0].local is True

    assert catalog[1].id == "openai/gpt-4"
    assert catalog[1].input_per_mtok == 10.0

    assert catalog[2].id == "gpt-4"
    assert catalog[2].input_per_mtok == 20.0
    assert catalog[2].provider == "openrouter"  # openrouter preferred over litellm
