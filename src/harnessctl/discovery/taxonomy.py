import httpx
import msgpack
import zstandard as zstd
from typing import Dict, Any, Optional

DEFAULT_TAXONOMY_URL = "https://github.com/dragoscirjan/harness-taxonomy/releases/latest/download/taxonomy.msgpack.zst"


class TaxonomyClient:
    def __init__(self, url: str = DEFAULT_TAXONOMY_URL):
        self.url = url
        self._cache: Optional[Dict[str, Any]] = None

    def fetch(self, force: bool = False) -> Dict[str, Any]:
        """Fetch the taxonomy registry from GitHub releases."""
        if self._cache and not force:
            return self._cache

        response = httpx.get(self.url, follow_redirects=True)
        response.raise_for_status()

        # Decompress zstd
        dctx = zstd.ZstdDecompressor()
        decompressed_data = dctx.decompress(response.content)

        # Unpack msgpack
        self._cache = msgpack.unpackb(decompressed_data, raw=False)
        return self._cache

    def get_intent_complexity(self, query: str) -> float:
        """Evaluate intent complexity by matching query against taxonomy concepts."""
        taxonomy = self.fetch()
        score = 0.0
        query_lower = query.lower()

        for cat_name, cat_data in taxonomy.get("categories", {}).items():
            weight = cat_data.get("weight", 1.0)
            for group, concepts in cat_data.get("concepts", {}).items():
                for concept in concepts:
                    if concept.lower() in query_lower:
                        score += 10 * weight

        return min(score, 100.0)
