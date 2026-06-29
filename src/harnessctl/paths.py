"""Centralized filesystem path resolution utilities for harnessctl."""

from __future__ import annotations

import os
from pathlib import Path


def resolve_user_path(path: str | Path) -> Path:
    """Resolve a path with ``~`` expansion to an absolute, symlink-resolved path."""
    return Path(path).expanduser().resolve()


def get_global_config_base_dir() -> Path:
    """Return the global harnessctl config base directory.

    Resolution order:
    1. ``$HARNESSCTL_HOME``
    2. ``~/.config/harnessctl``
    """
    configured = os.environ.get("HARNESSCTL_HOME")
    if configured:
        return resolve_user_path(configured)
    return resolve_user_path(Path("~/.config/harnessctl"))


def resolve_project_root(project: str | Path | None = None) -> Path:
    """Resolve project root from ``--project``-style input.

    If ``project`` is ``None``, current working directory is used.
    """
    if project is None:
        return Path.cwd().resolve()
    return resolve_user_path(project)


def get_project_config_base_dir(project: str | Path | None = None) -> Path:
    """Return project-local harnessctl config base directory.

    This maps to ``<project-root>/.harnessctl``.
    """
    return resolve_project_root(project) / ".harnessctl"


def ensure_directory(path: str | Path) -> Path:
    """Create directory recursively if needed and return resolved path."""
    resolved = resolve_user_path(path)
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved
