"""Registry for versioned routing config schemas."""

from __future__ import annotations

from pathlib import Path

SCHEMA_BASE_DIR = Path(__file__).resolve().parents[3] / "schemas" / "config"

_API_VERSION_TO_SCHEMA = {
    "harnessctl/v1alpha1": "harnessctl-v1alpha1-routing.schema.json",
}


def get_schema_path_for_api_version(api_version: str) -> Path:
    """Return schema file path for a routing config ``apiVersion``.

    Raises:
        ValueError: If ``api_version`` is unknown.
    """
    schema_file = _API_VERSION_TO_SCHEMA.get(api_version)
    if schema_file is None:
        raise ValueError(f"Unsupported apiVersion: {api_version!r}")
    return (SCHEMA_BASE_DIR / schema_file).resolve()
