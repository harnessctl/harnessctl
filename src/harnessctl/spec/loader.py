"""Load and deep-merge harnessctl spec from multiple YAML sources."""

from pathlib import Path
from typing import Any

import yaml

from harnessctl.paths import get_global_config_base_dir, get_project_config_base_dir
from harnessctl.spec.models import Spec

_KEYED_LIST_MERGE_FIELDS = {"agents", "rules", "chains"}
_KEY_CANDIDATES = ("id", "name")


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file into a dict; return empty dict if file missing or empty."""
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data if isinstance(data, dict) else {}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge *override* into *base*.

    Dicts are merged deeply; scalars are replaced outright.
    Lists are replaced, except keyed list fields (``agents``, ``rules``,
    ``chains``) which merge by ``id``/``name`` when possible.
    """
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        elif (
            key in _KEYED_LIST_MERGE_FIELDS
            and isinstance(value, list)
            and isinstance(merged.get(key), list)
        ):
            merged[key] = _merge_keyed_list(merged[key], value)
        else:
            merged[key] = value
    return merged


def _entry_identity(entry: Any) -> str | None:
    if not isinstance(entry, dict):
        return None
    for candidate in _KEY_CANDIDATES:
        identifier = entry.get(candidate)
        if isinstance(identifier, str) and identifier:
            return f"{candidate}:{identifier}"
    return None


def _merge_keyed_list(base: list[Any], override: list[Any]) -> list[Any]:
    """Merge lists by entry identity (``id`` or ``name``) when possible.

    If either list contains entries without identity, fallback is full replacement
    with the higher-precedence list (*override*).
    """
    base_ids = [_entry_identity(item) for item in base]
    override_ids = [_entry_identity(item) for item in override]
    if any(identifier is None for identifier in base_ids + override_ids):
        return list(override)

    duplicate_base_ids = {
        identifier for identifier in base_ids if base_ids.count(identifier) > 1
    }
    if duplicate_base_ids:
        duplicates = ", ".join(
            sorted(str(identifier) for identifier in duplicate_base_ids)
        )
        raise ValueError(f"Duplicate keyed-list identities in base list: {duplicates}")

    merged = [dict(item) if isinstance(item, dict) else item for item in base]
    index_by_id = {identifier: index for index, identifier in enumerate(base_ids)}

    for item, identifier in zip(override, override_ids):
        if identifier in index_by_id:
            base_index = index_by_id[identifier]
            existing = merged[base_index]
            if isinstance(existing, dict) and isinstance(item, dict):
                merged[base_index] = _deep_merge(existing, item)
            else:
                merged[base_index] = item
        else:
            merged.append(item)
    return merged


def _default_defaults_path() -> Path | None:
    """Path to built-in defaults YAML, if it exists."""
    candidate = Path(__file__).parent / "defaults" / "defaults.yaml"
    return candidate if candidate.exists() else None


def _default_user_config_path() -> Path | None:
    """Path to user-level config YAML."""
    home = get_global_config_base_dir()
    candidate = home / "config.yaml"
    return candidate if candidate.exists() else None


def _default_project_local_path() -> Path | None:
    """Path to project-local config YAML."""
    candidate = get_project_config_base_dir() / "config.yaml"
    return candidate if candidate.exists() else None


def load_spec(
    cli_overrides: dict[str, Any] | None = None,
    *,
    defaults_path: Path | None = None,
    user_config_path: Path | None = None,
    project_local_path: Path | None = None,
) -> Spec:
    """Load and merge YAML spec sources into a Pydantic ``Spec``.

    Merge order (lowest → highest precedence):
        1. built-in defaults
        2. user config (``~/.config/harnessctl/config.yaml`` or ``$HARNESSCTL_HOME/config.yaml``)
        3. project-local config (``.harnessctl/config.yaml``)
        4. *cli_overrides* dict

    Missing files are silently skipped. Dicts are merged deeply; lists and
    scalars are replaced by the higher-precedence source.
    """
    if defaults_path is None:
        defaults_path = _default_defaults_path()
    if user_config_path is None:
        user_config_path = _default_user_config_path()
    if project_local_path is None:
        project_local_path = _default_project_local_path()

    merged: dict[str, Any] = {}

    for path in (defaults_path, user_config_path, project_local_path):
        if path is not None:
            merged = _deep_merge(merged, _load_yaml(path))

    if cli_overrides:
        merged = _deep_merge(merged, cli_overrides)

    return Spec.model_validate(merged)
