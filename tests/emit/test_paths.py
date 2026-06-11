"""Tests for harnessctl.emit.paths."""

import os
from pathlib import Path

import pytest

from harnessctl.emit.paths import resolve_path


class TestResolvePath:
    def test_plain_absolute_path(self) -> None:
        assert resolve_path("/foo/bar") == "/foo/bar"

    def test_expands_tilde(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HOME", "/home/alice")
        assert resolve_path("~/config") == "/home/alice/config"

    def test_expands_project(self, tmp_path: Path) -> None:
        project = str(tmp_path / "proj")
        assert resolve_path("{project}/.opencode", project_dir=project) == str(
            (tmp_path / "proj" / ".opencode").resolve()
        )

    def test_missing_project_raises(self) -> None:
        with pytest.raises(ValueError, match="project_dir"):
            resolve_path("{project}/.opencode")

    def test_expands_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("MY_VAR", "/var/value")
        assert resolve_path("${env:MY_VAR}/file") == "/var/value/file"

    def test_missing_env_var_raises(self) -> None:
        # Ensure the variable is not set.
        os.environ.pop("MISSING_VAR", None)
        with pytest.raises(ValueError, match="MISSING_VAR"):
            resolve_path("${env:MISSING_VAR}/file")

    def test_complex_template(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        monkeypatch.setenv("HARNESS_HOME", "/opt/harness")
        project = str(tmp_path / "proj")
        result = resolve_path(
            "~/${env:HARNESS_HOME}/{project}/config",
            project_dir=project,
        )
        # Resolve the expected path the same way resolve_path does.
        expected = str(
            Path(f"~/opt/harness/{tmp_path}/proj/config").expanduser().resolve()
        )
        assert result == expected

    def test_returns_absolute_for_relative(self, tmp_path: Path) -> None:
        # When given a relative path without ~/{project}/${env:}, it should
        # resolve against cwd.
        relative = "some/relative/path"
        result = resolve_path(relative)
        assert Path(result).is_absolute()
        assert result == str(Path(relative).resolve())
