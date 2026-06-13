import json
import os
import time
from pathlib import Path
from typing import Optional, Dict, Any

CACHE_DIR = Path(os.path.expanduser("~/.cache/harnessctl/pricing"))


def get_cache_path(source: str) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{source}.json"


def read_cache(source: str, ttl_hours: int) -> Optional[Dict[str, Any]]:
    path = get_cache_path(source)
    if not path.exists():
        return None

    mtime = path.stat().st_mtime
    now = time.time()

    if (now - mtime) > ttl_hours * 3600:
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def read_stale_cache(source: str) -> Optional[Dict[str, Any]]:
    path = get_cache_path(source)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def write_cache(source: str, data: Dict[str, Any]) -> None:
    path = get_cache_path(source)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def clear_cache() -> None:
    """Clear all pricing cache files."""
    if CACHE_DIR.exists():
        for f in CACHE_DIR.glob("*.json"):
            try:
                f.unlink()
            except Exception:
                pass
