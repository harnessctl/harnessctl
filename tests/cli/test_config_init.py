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


def test_init_global_creates_single_config_file(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["config", "init", "--provider", "github-copilot", "--global"],
        env={"HARNESSCTL_HOME": str(tmp_path / "global-home")},
    )
    assert result.exit_code == 0

    config = tmp_path / "global-home" / "config.yaml"
    assert config.exists()

    config_doc = _read_yaml(config)
    assert config_doc["apiVersion"] == "harnessctl/v1alpha1"
    assert config_doc["kind"] == "RoutingConfig"
    agents = config_doc["spec"]["agent_registry"]["agents"]
    assert len(agents) >= 5
    assert agents[0]["provider"] == "github-copilot"
    assert any(agent["model"] == "github-copilot/gpt-5.4" for agent in agents)
    assert any(agent.get("cost_band") == "draconic" for agent in agents)

    taxonomy = config_doc["spec"]["taxonomy"]
    assert "frontend" in taxonomy["task_classes"]
    assert taxonomy["aliases"]["ui"] == "frontend"

    rule_names = [rule["name"] for rule in config_doc["spec"]["routing"]["rules"]]
    assert "security-critical" in rule_names
    assert config_doc["spec"]["provider_presets"] == ["github-copilot"]


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

    config = project / ".harnessctl" / "config.yaml"
    assert config.exists()

    config_doc = _read_yaml(config)
    agents = config_doc["spec"]["agent_registry"]["agents"]
    assert len(agents) >= 3
    assert agents[0]["provider"] == "openrouter"
    assert any(agent["tier"] == "reasoning" for agent in agents)
    assert any(agent.get("cost_band") == "draconic" for agent in agents)

    rule_names = [rule["name"] for rule in config_doc["spec"]["routing"]["rules"]]
    assert "architecture-security" in rule_names
    assert config_doc["spec"]["provider_presets"] == ["openrouter"]


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
