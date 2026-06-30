"""Tests for `harnessctl prompts install` command behavior."""

from __future__ import annotations

from pathlib import Path

import yaml

from typer.testing import CliRunner

from harnessctl.cli import app

runner = CliRunner()


def _write_harnessctl_config(home: Path) -> None:
    config_dir = home
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "apiVersion": "harnessctl/v1alpha1",
                "kind": "RoutingConfig",
                "metadata": {"name": "default"},
                "spec": {
                    "taxonomy": {
                        "task_classes": ["implementation", "review", "docs"],
                        "aliases": {},
                    },
                    "agent_registry": {
                        "agents": [
                            {
                                "id": "backend-dev",
                                "model": "github-copilot/gpt-5.4-mini",
                                "provider": "github-copilot",
                                "tier": "medium",
                                "capabilities": ["implementation", "review"],
                            },
                            {
                                "id": "security-reviewer",
                                "model": "github-copilot/o3",
                                "provider": "github-copilot",
                                "tier": "reasoning",
                                "capabilities": ["review", "security_analysis"],
                            },
                        ]
                    },
                    "routing": {
                        "rules": [
                            {
                                "name": "default-rule",
                                "when": {
                                    "task_type_in": ["implementation", "review", "docs"]
                                },
                                "choose": {
                                    "preferred_tiers": ["cheap", "medium", "strong"],
                                    "optimize_for": "cost",
                                },
                            }
                        ]
                    },
                    "escalation": {
                        "strategy": {
                            "keying": "task_class",
                            "fallback_on_unknown_task_class": "default",
                        },
                        "chains": [
                            {"name": "default", "tiers": ["cheap", "medium", "strong"]}
                        ],
                    },
                    "provider_presets": ["github-copilot"],
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


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
    _write_harnessctl_config(tmp_path / "hctl-home")
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
        env={"HARNESSCTL_HOME": str(tmp_path / "hctl-home"), "HOME": str(home)},
    )
    assert result.exit_code == 0

    opencode_agents_dir = home / ".config" / "opencode" / "agents"
    orchestrator = opencode_agents_dir / "orchestrator.md"
    backend_dev = opencode_agents_dir / "backend-dev.md"
    security_reviewer = opencode_agents_dir / "security-reviewer.md"

    assert orchestrator.exists()
    assert backend_dev.exists()
    assert security_reviewer.exists()
    assert "mode: subagent" in orchestrator.read_text(encoding="utf-8")
    assert "You are the orchestrator." in orchestrator.read_text(encoding="utf-8")
    assert "model: github-copilot/gpt-5.4-mini" in backend_dev.read_text(
        encoding="utf-8"
    )


def test_install_global_pi_harness_writes_native_pi_paths(tmp_path: Path) -> None:
    _write_harnessctl_config(tmp_path / "hctl-home")
    home = tmp_path / "global-home"

    result = runner.invoke(
        app,
        [
            "prompts",
            "install",
            "--harness",
            "pi",
            "--version",
            "v1",
            "--global",
        ],
        env={"HARNESSCTL_HOME": str(tmp_path / "hctl-home"), "HOME": str(home)},
    )
    assert result.exit_code == 0

    pi_agents_dir = home / ".pi" / "agent" / "agents"
    assert (pi_agents_dir / "orchestrator.md").exists()
    assert (pi_agents_dir / "backend-dev.md").exists()
    assert "name: orchestrator" in (pi_agents_dir / "orchestrator.md").read_text(
        encoding="utf-8"
    )


def test_install_project_multiple_harnesses(tmp_path: Path) -> None:
    _write_harnessctl_config(tmp_path / "hctl-home")
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
        env={"HARNESSCTL_HOME": str(tmp_path / "hctl-home")},
    )
    assert result.exit_code == 0

    opencode_agents = project / ".opencode" / "agents"
    assert (opencode_agents / "orchestrator.md").exists()
    assert (opencode_agents / "backend-dev.md").exists()

    pi_agents = project / ".pi" / "agents"
    assert (pi_agents / "orchestrator.md").exists()
    assert (pi_agents / "backend-dev.md").exists()
    assert "name: backend-dev" in (pi_agents / "backend-dev.md").read_text(
        encoding="utf-8"
    )


def test_install_respects_overwrite_policy(tmp_path: Path) -> None:
    _write_harnessctl_config(tmp_path / "hctl-home")
    home = tmp_path / "global-home"
    env = {"HARNESSCTL_HOME": str(tmp_path / "hctl-home"), "HOME": str(home)}

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


def test_rejects_unsafe_version_segment(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "prompts",
            "install",
            "--harness",
            "opencode",
            "--version",
            "../v1",
            "--project",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 2
    assert "safe path segment" in result.stdout
