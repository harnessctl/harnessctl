import httpx
import msgpack
import zstandard as zstd
from typing import Dict, Any, Optional
from pathlib import Path
import os
import hashlib


def get_taxonomy_url(version: str) -> str:
    if version == "latest":
        return "https://github.com/harnessctl/harness-taxonomy/releases/latest/download/taxonomy.msgpack.zst"
    return f"https://github.com/harnessctl/harness-taxonomy/releases/download/{version}/taxonomy.msgpack.zst"


def get_cache_dir() -> Path:
    cache_dir = (
        Path(os.path.expanduser("~")) / ".local" / "share" / "harnessctl" / "taxonomy"
    )
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


class TaxonomyClient:
    def __init__(self, version: str = "latest"):
        self.version = version
        self.url = get_taxonomy_url(version)
        self._cache: Optional[Dict[str, Any]] = None

    def fetch(self, force: bool = False) -> Dict[str, Any]:
        """Fetch the taxonomy registry from GitHub releases or local cache."""
        if self._cache and not force:
            return self._cache

        cache_dir = get_cache_dir()

        # HEAD request to get the redirect and etag/hash
        try:
            head_resp = httpx.head(self.url, follow_redirects=True, timeout=5.0)
            head_resp.raise_for_status()

            # Use ETag if available, else fallback to version + content-length
            etag = head_resp.headers.get("etag", "").strip('"')
            if not etag:
                content_len = head_resp.headers.get("content-length", "0")
                etag = hashlib.md5(f"{self.version}-{content_len}".encode()).hexdigest()

            cache_file = cache_dir / f"{etag}.msgpack.zst"

            if cache_file.exists() and not force:
                with open(cache_file, "rb") as f:
                    compressed_content = f.read()
            else:
                resp = httpx.get(head_resp.url, follow_redirects=True)
                resp.raise_for_status()
                compressed_content = resp.content

                # Save to cache
                with open(cache_file, "wb") as f:
                    f.write(compressed_content)

        except httpx.HTTPError:
            # Fallback to local files if offline
            files = list(cache_dir.glob("*.msgpack.zst"))
            if files:
                # Use most recently modified cache file
                files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                with open(files[0], "rb") as f:
                    compressed_content = f.read()
            else:
                return {"categories": {}}

        # Decompress zstd
        dctx = zstd.ZstdDecompressor()
        decompressed_data = dctx.decompress(compressed_content)

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
