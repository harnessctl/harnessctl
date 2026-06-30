"""Tests for `harnessctl prompts render` command behavior."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from harnessctl.cli import app

runner = CliRunner()


def test_render_requires_cli_flag() -> None:
    result = runner.invoke(
        app,
        ["prompts", "render", "--harness", "opencode", "--version", "v1"],
    )
    assert result.exit_code == 2
    assert "requires --cli" in result.stdout


def test_render_outputs_multiple_harness_sections() -> None:
    result = runner.invoke(
        app,
        [
            "prompts",
            "render",
            "--harness",
            "opencode",
            "--harness",
            "pi",
            "--version",
            "v1",
            "--cli",
        ],
    )
    assert result.exit_code == 0
    assert "harness: opencode" in result.stdout
    assert "harness: pi" in result.stdout
    assert "---" in result.stdout


def test_render_injects_template_variables() -> None:
    result = runner.invoke(
        app,
        [
            "prompts",
            "render",
            "--harness",
            "opencode",
            "--version",
            "v1",
            "--cli",
            "--var",
            "tone=direct",
        ],
    )
    assert result.exit_code == 0
    assert "tone: direct" in result.stdout


def test_render_rejects_invalid_var_format() -> None:
    result = runner.invoke(
        app,
        [
            "prompts",
            "render",
            "--harness",
            "opencode",
            "--version",
            "v1",
            "--cli",
            "--var",
            "tone",
        ],
    )
    assert result.exit_code == 2
    assert "Expected KEY=VALUE" in result.stdout


def test_render_does_not_write_filesystem(tmp_path: Path) -> None:
    home = tmp_path / "global-home"
    result = runner.invoke(
        app,
        ["prompts", "render", "--harness", "opencode", "--version", "v1", "--cli"],
        env={"HARNESSCTL_HOME": str(home)},
    )
    assert result.exit_code == 0
    assert not home.exists()
