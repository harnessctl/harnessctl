"""Load and deep-merge harnessctl spec from multiple YAML sources."""

import os
from pathlib import Path
from typing import Any

import yaml

from harnessctl.spec.models import Spec


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file into a dict; return empty dict if file missing or empty."""
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data if isinstance(data, dict) else {}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge *override* into *base*.

    Dicts are merged deeply; scalars and lists are replaced outright.
    """
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _default_defaults_path() -> Path | None:
    """Path to built-in defaults YAML, if it exists."""
    candidate = Path(__file__).parent / "defaults" / "defaults.yaml"
    return candidate if candidate.exists() else None


def _default_user_config_path() -> Path | None:
    """Path to user-level config YAML."""
    home = Path(
        os.environ.get("HARNESSCTL_HOME", Path.home() / ".config" / "harnessctl")
    )
    candidate = home / "config.yaml"
    return candidate if candidate.exists() else None


def _default_project_local_path() -> Path | None:
    """Path to project-local config YAML."""
    candidate = Path.cwd() / ".harnessctl" / "config.yaml"
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
