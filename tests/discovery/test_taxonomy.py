from harnessctl.discovery.taxonomy import TaxonomyClient
import msgpack
import zstandard as zstd
from httpx import Response


def test_taxonomy_client(respx_mock):
    # Create fake taxonomy
    fake_taxonomy = {
        "categories": {"coding": {"weight": 1.0, "concepts": {"solid": ["liskov"]}}}
    }

    packed = msgpack.packb(fake_taxonomy, use_bin_type=True)
    cctx = zstd.ZstdCompressor(level=1)
    compressed = cctx.compress(packed)

    respx_mock.get(
        "https://github.com/dragoscirjan/harness-taxonomy/releases/latest/download/taxonomy.msgpack.zst"
    ).mock(return_value=Response(200, content=compressed))

    client = TaxonomyClient()
    data = client.fetch()

    assert data["categories"]["coding"]["weight"] == 1.0

    score = client.get_intent_complexity("I want to use liskov substitution")
    assert score == 10.0
