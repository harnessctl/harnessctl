"""Registry for versioned routing config schemas."""

from __future__ import annotations

from importlib import resources
from pathlib import Path

_API_VERSION_TO_SCHEMA = {
    "harnessctl/v1alpha1": "harnessctl-v1alpha1-routing.schema.json",
}


def _package_schema_base_dir() -> Path | None:
    candidate = resources.files("harnessctl").joinpath("schemas", "config")
    if candidate.is_dir():
        return Path(str(candidate)).resolve()
    return None


def _source_schema_base_dir() -> Path:
    return (Path(__file__).resolve().parents[1] / "schemas" / "config").resolve()


def get_schema_path_for_api_version(api_version: str) -> Path:
    """Return schema file path for a routing config ``apiVersion``.

    Raises:
        ValueError: If ``api_version`` is unknown.
    """
    schema_file = _API_VERSION_TO_SCHEMA.get(api_version)
    if schema_file is None:
        raise ValueError(f"Unsupported apiVersion: {api_version!r}")

    package_base_dir = _package_schema_base_dir()
    if package_base_dir is not None:
        package_path = package_base_dir / schema_file
        if package_path.is_file():
            return package_path

    return _source_schema_base_dir() / schema_file
