"""Integration-style tests for MCP select_model_for_task contract."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner
import yaml

from harnessctl.cli import app

runner = CliRunner()


def _write_config(path: Path) -> None:
    config = {
        "apiVersion": "harnessctl/v1alpha1",
        "kind": "RoutingConfig",
        "metadata": {"name": "test"},
        "spec": {
            "taxonomy": {"task_classes": ["lld"]},
            "policies": {
                "risk": {"min_tier_by_task_class": {"lld": "medium"}},
                "constraints": {
                    "allow_unverified_models": False,
                    "allow_preview_models": True,
                },
            },
            "agent_registry": {
                "agents": [
                    {
                        "id": "agent-cheap",
                        "model": "m/cheap",
                        "provider": "openrouter",
                        "tier": "medium",
                        "capabilities": ["design", "reasoning"],
                        "cost": {
                            "estimated_cost_usd": 0.2,
                            "success_probability": 0.5,
                        },
                    },
                    {
                        "id": "agent-strong",
                        "model": "m/strong",
                        "provider": "openrouter",
                        "tier": "strong",
                        "capabilities": ["design", "reasoning"],
                        "cost": {
                            "estimated_cost_usd": 0.3,
                            "success_probability": 0.9,
                        },
                    },
                    {
                        "id": "agent-reason",
                        "model": "m/reason",
                        "provider": "openrouter",
                        "tier": "reasoning",
                        "capabilities": ["design", "reasoning"],
                        "cost": {
                            "estimated_cost_usd": 0.5,
                            "success_probability": 0.95,
                        },
                    },
                ]
            },
            "routing": {
                "rules": [
                    {
                        "name": "lld-design",
                        "when": {"task_type_in": ["lld"], "max_complexity": 100},
                        "choose": {
                            "preferred_tiers": ["medium", "strong", "reasoning"],
                            "optimize_for": "cost_per_success",
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
                    {"name": "default", "tiers": ["medium", "strong", "reasoning"]},
                    {"name": "lld", "tiers": ["medium", "strong", "reasoning"]},
                ],
                "failure_policies": {
                    "wrong_solution": {"action": "escalate_next_tier"}
                },
            },
        },
    }
    path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")


def test_select_model_for_task_returns_agent_first_contract(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    _write_config(config_file)
    request = {
        "prompt": "Design an LLD for distributed lock manager",
        "task_type": "lld",
        "constraints": {"user_required_capabilities": ["design", "reasoning"]},
        "hints": {"complexity": 70},
    }

    result = runner.invoke(
        app,
        [
            "mcp",
            "select_model_for_task",
            "--request-json",
            json.dumps(request),
            "--config-file",
            str(config_file),
        ],
    )
    assert result.exit_code == 0

    payload = json.loads(result.stdout)
    assert payload["selected_agent"] == "agent-strong"
    assert payload["selected_model"] == "m/strong"
    assert payload["selected_provider"] == "openrouter"
    assert payload["selected_tier"] == "strong"
    assert isinstance(payload["fallback_agents"], list)
    assert payload["trace"]["selection_strategy"] == "deterministic_cost_per_success"
    assert payload["trace"]["matched_rules"] == ["lld-design"]
    assert payload["trace"]["derived"]["task_class"] == "lld"
    assert payload["trace"]["provenance"]["task_class"] == "caller_hint"


def test_select_model_for_task_returns_policy_failure_payload(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    _write_config(config_file)
    request = {
        "prompt": "Design an LLD for distributed lock manager",
        "task_type": "lld",
        "constraints": {
            "provider_allowlist": ["github-copilot"],
            "user_required_capabilities": ["design", "reasoning"],
        },
    }

    result = runner.invoke(
        app,
        [
            "mcp",
            "select_model_for_task",
            "--request-json",
            json.dumps(request),
            "--config-file",
            str(config_file),
        ],
    )
    assert result.exit_code == 0

    payload = json.loads(result.stdout)
    assert payload["error"]["code"] == "PROVIDER_BLOCKED"
    assert payload["error"]["details"]["gate"] == "provider_allowlist"
    assert payload["trace"]["derived"]["task_class"] == "lld"


def test_select_model_for_task_rejects_request_file_directory(tmp_path: Path) -> None:
    config_file = tmp_path / "config.yaml"
    _write_config(config_file)

    request_dir = tmp_path / "request-dir"
    request_dir.mkdir()

    result = runner.invoke(
        app,
        [
            "mcp",
            "select_model_for_task",
            "--request-file",
            str(request_dir),
            "--config-file",
            str(config_file),
        ],
    )
    assert result.exit_code == 2
    assert "not a regular file" in result.stdout


def test_select_model_for_task_matches_rules_using_derived_task_class(
    tmp_path: Path,
) -> None:
    config_file = tmp_path / "config.yaml"
    config = {
        "apiVersion": "harnessctl/v1alpha1",
        "kind": "RoutingConfig",
        "metadata": {"name": "task-class-derived"},
        "spec": {
            "taxonomy": {
                "task_classes": ["frontend"],
                "aliases": {"ui": "frontend"},
            },
            "policies": {
                "risk": {"min_tier_by_task_class": {"frontend": "medium"}},
                "constraints": {
                    "allow_unverified_models": False,
                    "allow_preview_models": True,
                },
            },
            "agent_registry": {
                "agents": [
                    {
                        "id": "frontend-agent",
                        "model": "m/frontend",
                        "provider": "openrouter",
                        "tier": "medium",
                        "capabilities": ["implementation", "review"],
                        "cost": {"estimated_cost_usd": 0.2},
                    }
                ]
            },
            "routing": {
                "rules": [
                    {
                        "name": "frontend-rule",
                        "when": {"task_type_in": ["frontend"], "max_complexity": 100},
                        "choose": {
                            "preferred_tiers": ["medium"],
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
                    {"name": "default", "tiers": ["medium"]},
                    {"name": "frontend", "tiers": ["medium"]},
                ],
                "failure_policies": {
                    "wrong_solution": {"action": "escalate_next_tier"}
                },
            },
        },
    }
    config_file.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    request = {
        "prompt": "Need UI updates in forms and interaction flow",
        "task_type": "ui",
        "constraints": {"user_required_capabilities": ["implementation", "review"]},
    }

    result = runner.invoke(
        app,
        [
            "mcp",
            "select_model_for_task",
            "--request-json",
            json.dumps(request),
            "--config-file",
            str(config_file),
        ],
    )
    assert result.exit_code == 0

    payload = json.loads(result.stdout)
    assert payload["trace"]["derived"]["task_class"] == "frontend"
    assert payload["trace"]["provenance"]["task_class"] == "caller_hint_alias"
    assert payload["trace"]["matched_rules"] == ["frontend-rule"]
