"""Tests for centralized path resolution utilities."""

from __future__ import annotations

from pathlib import Path

import pytest

from harnessctl.paths import (
    ensure_directory,
    get_global_config_base_dir,
    get_project_config_base_dir,
    resolve_project_root,
)


def test_get_global_config_base_dir_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HARNESSCTL_HOME", raising=False)
    monkeypatch.setenv("HOME", "/home/alice")
    assert get_global_config_base_dir() == Path("/home/alice/.config/harnessctl")


def test_get_global_config_base_dir_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HARNESSCTL_HOME", "~/custom-harnessctl")
    monkeypatch.setenv("HOME", "/home/alice")
    assert get_global_config_base_dir() == Path("/home/alice/custom-harnessctl")


def test_get_global_config_base_dir_empty_env_falls_back_to_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HARNESSCTL_HOME", "")
    monkeypatch.setenv("HOME", "/home/alice")
    assert get_global_config_base_dir() == Path("/home/alice/.config/harnessctl")


def test_resolve_project_root_from_dot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    assert resolve_project_root(".") == tmp_path.resolve()


def test_resolve_project_root_uses_cwd_when_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    assert resolve_project_root(None) == tmp_path.resolve()


def test_resolve_project_root_from_absolute(tmp_path: Path) -> None:
    project = tmp_path / "my-project"
    assert resolve_project_root(str(project)) == project.resolve()


def test_get_project_config_base_dir(tmp_path: Path) -> None:
    project = tmp_path / "my-project"
    expected = (project / ".harnessctl").resolve()
    assert get_project_config_base_dir(project) == expected


def test_ensure_directory_creates_missing_tree(tmp_path: Path) -> None:
    created = ensure_directory(tmp_path / "a" / "b" / "c")
    assert created.is_dir()
    assert created == (tmp_path / "a" / "b" / "c").resolve()


def test_ensure_directory_is_idempotent(tmp_path: Path) -> None:
    target = tmp_path / "stable" / "dir"
    first = ensure_directory(target)
    second = ensure_directory(target)
    assert first == second
    assert second.is_dir()
