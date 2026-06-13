import httpx
from typing import Dict, Any, Optional
from harnessctl.pricing.cache import read_cache, read_stale_cache
from harnessctl.spec.warnings import WarningCollector


async def fetch_prices_generic(
    provider_name: str,
    url: str,
    warnings: WarningCollector,
    force_refresh: bool = False,
    ttl_hours: int = 24,
) -> Optional[Dict[str, Any]]:
    """Generic price fetcher with caching and error handling."""
    if not force_refresh:
        cached = read_cache(provider_name, ttl_hours=ttl_hours)
        if cached is not None:
            return cached

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            from harnessctl.pricing.cache import write_cache

            write_cache(provider_name, data)
            return data
        except Exception as e:
            warnings.add_warning(
                f"Failed to fetch {provider_name} prices: {e}. Falling back to stale cache."
            )
            return read_stale_cache(provider_name)
