"""Tests for `harnessctl prompts install` command behavior."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from harnessctl.cli import app

runner = CliRunner()


def _prompt_file(base: Path, harness: str, version: str = "v1") -> Path:
    return base / "prompts" / harness / version / "orchestrator.md"


def test_requires_exactly_one_target(tmp_path: Path) -> None:
    missing = runner.invoke(app, ["prompts", "install", "--harness", "opencode"])
    assert missing.exit_code == 2
    assert "exactly one target" in missing.stdout

    both = runner.invoke(
        app,
        [
            "prompts",
            "install",
            "--harness",
            "opencode",
            "--global",
            "--project",
            str(tmp_path),
        ],
    )
    assert both.exit_code == 2
    assert "exactly one target" in both.stdout


def test_install_global_single_harness(tmp_path: Path) -> None:
    home = tmp_path / "global-home"
    result = runner.invoke(
        app,
        [
            "prompts",
            "install",
            "--harness",
            "opencode",
            "--version",
            "v1",
            "--global",
        ],
        env={"HARNESSCTL_HOME": str(home)},
    )
    assert result.exit_code == 0

    output = _prompt_file(home, "opencode")
    assert output.exists()
    assert "harness: opencode" in output.read_text(encoding="utf-8")


def test_install_project_multiple_harnesses(tmp_path: Path) -> None:
    project = tmp_path / "project"
    result = runner.invoke(
        app,
        [
            "prompts",
            "install",
            "--harness",
            "opencode",
            "--harness",
            "pi",
            "--project",
            str(project),
        ],
    )
    assert result.exit_code == 0

    project_base = project / ".harnessctl"
    assert _prompt_file(project_base, "opencode").exists()
    assert _prompt_file(project_base, "pi").exists()


def test_install_respects_overwrite_policy(tmp_path: Path) -> None:
    home = tmp_path / "global-home"
    env = {"HARNESSCTL_HOME": str(home)}

    first = runner.invoke(
        app,
        ["prompts", "install", "--harness", "opencode", "--global"],
        env=env,
    )
    assert first.exit_code == 0

    second = runner.invoke(
        app,
        ["prompts", "install", "--harness", "opencode", "--global"],
        env=env,
    )
    assert second.exit_code == 2
    assert "Refusing to overwrite" in second.stdout

    third = runner.invoke(
        app,
        [
            "prompts",
            "install",
            "--harness",
            "opencode",
            "--global",
            "--overwrite",
        ],
        env=env,
    )
    assert third.exit_code == 0


def test_rejects_unknown_harness(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "prompts",
            "install",
            "--harness",
            "unknown-harness",
            "--project",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 2
    assert "Unsupported harness" in result.stdout
