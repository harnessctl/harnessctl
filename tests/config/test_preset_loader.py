"""Tests for provider preset loading and derived bootstrap documents."""

from __future__ import annotations

import pytest

from harnessctl.config.preset_loader import (
    build_provider_reference_from_preset,
    build_routing_config_from_preset,
    load_provider_preset,
)


def test_load_provider_preset_returns_packaged_doc() -> None:
    preset = load_provider_preset("github-copilot")
    assert preset["kind"] == "ProviderPreset"
    assert preset["metadata"]["name"] == "github-copilot"


def test_build_routing_config_from_preset_wires_agent_defaults() -> None:
    routing_doc = build_routing_config_from_preset("openrouter")
    assert routing_doc["apiVersion"] == "harnessctl/v1alpha1"
    agents = routing_doc["spec"]["agent_registry"]["agents"]
    assert len(agents) >= 3
    assert any(agent["provider"] == "openrouter" for agent in agents)
    assert any(agent["tier"] == "reasoning" for agent in agents)
    assert any(agent.get("cost_band") == "draconic" for agent in agents)

    task_classes = routing_doc["spec"]["taxonomy"]["task_classes"]
    assert "frontend" in task_classes
    assert "architecture" in task_classes

    rule_names = [rule["name"] for rule in routing_doc["spec"]["routing"]["rules"]]
    assert "architecture-security" in rule_names


def test_build_provider_reference_uses_preset_metadata() -> None:
    provider_doc = build_provider_reference_from_preset("github-copilot")
    assert provider_doc["metadata"]["name"] == "github-copilot"
    assert provider_doc["spec"]["provider"] == "github-copilot"


def test_unknown_provider_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unsupported provider"):
        load_provider_preset("unknown")
