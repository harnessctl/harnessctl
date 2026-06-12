from typing import Optional
from dataclasses import dataclass


@dataclass
class ModelSource:
    type: str  # "hf", "ollama", "url"
    repo: str
    file: Optional[str] = None
    url: Optional[str] = None


def parse_source(source_str: str) -> ModelSource:
    """Parse source string into ModelSource object."""
    if source_str.startswith("hf:"):
        parts = source_str[3:].split(":")
        repo = parts[0]
        file = parts[1] if len(parts) > 1 else None
        return ModelSource(type="hf", repo=repo, file=file)

    if source_str.startswith("ollama:"):
        name = source_str[7:]
        return ModelSource(type="ollama", repo=name)

    if source_str.startswith("http://") or source_str.startswith("https://"):
        # Use last part of URL as repo name for hash/storage
        return ModelSource(type="url", repo=source_str.split("/")[-1], url=source_str)

    raise ValueError(f"Invalid source format: {source_str}")
