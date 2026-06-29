"""Tests for `harnessctl config init` command behavior."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner
import yaml

from harnessctl.cli import app

runner = CliRunner()


def _read_yaml(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data if isinstance(data, dict) else {}


def test_requires_exactly_one_target(tmp_path: Path) -> None:
    missing = runner.invoke(
        app,
        ["config", "init", "--provider", "github-copilot"],
    )
    assert missing.exit_code == 2
    assert "exactly one target" in missing.stdout

    result = runner.invoke(
        app,
        [
            "config",
            "init",
            "--provider",
            "github-copilot",
            "--global",
            "--project",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 2
    assert "exactly one target" in result.stdout


def test_init_global_creates_routing_and_provider_files(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["config", "init", "--provider", "github-copilot", "--global"],
        env={"HARNESSCTL_HOME": str(tmp_path / "global-home")},
    )
    assert result.exit_code == 0

    routing = tmp_path / "global-home" / "routing.yaml"
    provider = tmp_path / "global-home" / "providers" / "github-copilot.yaml"
    assert routing.exists()
    assert provider.exists()

    routing_doc = _read_yaml(routing)
    assert routing_doc["apiVersion"] == "harnessctl/v1alpha1"
    assert routing_doc["kind"] == "RoutingConfig"


def test_init_project_creates_files_under_project_harnessctl(tmp_path: Path) -> None:
    project = tmp_path / "project"
    result = runner.invoke(
        app,
        [
            "config",
            "init",
            "--provider",
            "openrouter",
            "--project",
            str(project),
        ],
    )
    assert result.exit_code == 0

    routing = project / ".harnessctl" / "routing.yaml"
    provider = project / ".harnessctl" / "providers" / "openrouter.yaml"
    assert routing.exists()
    assert provider.exists()


def test_init_fails_on_existing_without_overwrite(tmp_path: Path) -> None:
    env = {"HARNESSCTL_HOME": str(tmp_path / "global-home")}
    first = runner.invoke(
        app,
        ["config", "init", "--provider", "github-copilot", "--global"],
        env=env,
    )
    assert first.exit_code == 0

    second = runner.invoke(
        app,
        ["config", "init", "--provider", "github-copilot", "--global"],
        env=env,
    )
    assert second.exit_code == 2
    assert "Refusing to overwrite" in second.stdout


def test_init_overwrite_succeeds(tmp_path: Path) -> None:
    env = {"HARNESSCTL_HOME": str(tmp_path / "global-home")}
    first = runner.invoke(
        app,
        ["config", "init", "--provider", "openrouter", "--global"],
        env=env,
    )
    assert first.exit_code == 0

    second = runner.invoke(
        app,
        [
            "config",
            "init",
            "--provider",
            "openrouter",
            "--global",
            "--overwrite",
        ],
        env=env,
    )
    assert second.exit_code == 0


def test_rejects_unknown_provider(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["config", "init", "--provider", "unknown", "--project", str(tmp_path)],
    )
    assert result.exit_code == 2
    assert "Unsupported provider" in result.stdout
