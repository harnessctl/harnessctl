from harnessctl.discovery.taxonomy import TaxonomyClient, get_taxonomy_url
import msgpack
import zstandard as zstd
from httpx import Response


def test_taxonomy_client(respx_mock, tmp_path, monkeypatch):
    # Mock cache dir to temp
    monkeypatch.setattr("harnessctl.discovery.taxonomy.get_cache_dir", lambda: tmp_path)

    # Create fake taxonomy
    fake_taxonomy = {
        "categories": {"coding": {"weight": 1.0, "concepts": {"solid": ["liskov"]}}}
    }

    packed = msgpack.packb(fake_taxonomy, use_bin_type=True)
    cctx = zstd.ZstdCompressor(level=1)
    compressed = cctx.compress(packed)

    url = get_taxonomy_url("latest")

    # Mock HEAD
    respx_mock.head(url).mock(
        return_value=Response(200, headers={"etag": '"test-etag-123"'})
    )
    # Mock GET
    respx_mock.get(url).mock(return_value=Response(200, content=compressed))
    client = TaxonomyClient()
    data = client.fetch()

    assert data["categories"]["coding"]["weight"] == 1.0

    score = client.get_intent_complexity("I want to use liskov substitution")
    assert score == 10.0

    # Verify it was cached
    assert (tmp_path / "test-etag-123.msgpack.zst").exists()

    # Verify second fetch doesn't make a request (mock router will fail if it makes one)
    # Clear cache variable to force cache disk read
    client._cache = None
    respx_mock.clear()

    respx_mock.head(url).mock(
        return_value=Response(200, headers={"etag": '"test-etag-123"'})
    )
    # Get shouldn't be called because the etag file exists

    data2 = client.fetch()
    assert data2["categories"]["coding"]["weight"] == 1.0
