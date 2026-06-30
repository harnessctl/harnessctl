"""Tests for deterministic hard policy gates."""

from __future__ import annotations

import pytest

from harnessctl.routing.policy import PolicyGateError, apply_policy_gates


def _base_request() -> dict[str, object]:
    return {
        "prompt": "Implement auth middleware",
        "constraints": {},
        "context": {},
    }


def _base_derived() -> dict[str, object]:
    return {
        "derived": {
            "task_class": "backend",
            "required_capabilities": ["implementation"],
            "risk": "medium",
            "complexity": 40,
        }
    }


def _base_config() -> dict[str, object]:
    return {
        "spec": {
            "agent_registry": {
                "agents": [
                    {
                        "id": "agent-cheap",
                        "provider": "github-copilot",
                        "model": "github-copilot/gpt-5-mini",
                        "tier": "cheap",
                        "capabilities": ["implementation", "review"],
                        "cost": {"estimated_cost_usd": 0.2},
                    },
                    {
                        "id": "agent-strong",
                        "provider": "openrouter",
                        "model": "openrouter/anthropic/claude-3.5-sonnet",
                        "tier": "strong",
                        "capabilities": ["implementation", "review", "reasoning"],
                        "cost": {"estimated_cost_usd": 0.7},
                    },
                ]
            },
            "policies": {
                "risk": {
                    "min_tier_by_task_class": {
                        "security": "strong",
                    }
                }
            },
        }
    }


def test_policy_gates_provider_allowlist_first() -> None:
    request = _base_request()
    request["constraints"] = {
        "provider_allowlist": ["anthropic-only"],
        "max_cost_usd": 0.01,
    }

    with pytest.raises(PolicyGateError) as err:
        apply_policy_gates(
            request,
            derived_metadata=_base_derived(),
            routing_config=_base_config(),
        )

    assert err.value.code == "PROVIDER_BLOCKED"
    assert err.value.details["gate"] == "provider_allowlist"


def test_policy_gates_capabilities_before_risk_and_budget() -> None:
    derived = _base_derived()
    derived["derived"]["task_class"] = "security"
    derived["derived"]["required_capabilities"] = ["security_analysis"]

    request = _base_request()
    request["constraints"] = {"max_cost_usd": 0.01}

    with pytest.raises(PolicyGateError) as err:
        apply_policy_gates(
            request,
            derived_metadata=derived,
            routing_config=_base_config(),
        )

    assert err.value.code == "CAPABILITY_BLOCKED"
    assert err.value.details["gate"] == "capabilities"


def test_policy_gates_risk_floor_blocks_low_tier_agents() -> None:
    config = _base_config()
    # Remove strong candidate so security floor cannot be met.
    config["spec"]["agent_registry"]["agents"] = [
        config["spec"]["agent_registry"]["agents"][0]
    ]

    derived = _base_derived()
    derived["derived"]["task_class"] = "security"

    with pytest.raises(PolicyGateError) as err:
        apply_policy_gates(
            _base_request(),
            derived_metadata=derived,
            routing_config=config,
        )

    assert err.value.code == "RISK_BLOCKED"
    assert err.value.details["min_tier"] == "strong"


def test_policy_gates_budget_blocked_when_over_limit() -> None:
    request = _base_request()
    request["constraints"] = {"max_cost_usd": 0.1}

    with pytest.raises(PolicyGateError) as err:
        apply_policy_gates(
            request,
            derived_metadata=_base_derived(),
            routing_config=_base_config(),
        )

    assert err.value.code == "BUDGET_BLOCKED"
    assert err.value.details["gate"] == "budget"


def test_policy_gates_success_returns_filtered_candidates_and_checks() -> None:
    request = _base_request()
    request["constraints"] = {
        "provider_allowlist": ["github-copilot"],
        "max_cost_usd": 0.3,
    }

    result = apply_policy_gates(
        request,
        derived_metadata=_base_derived(),
        routing_config=_base_config(),
    )

    assert [candidate["id"] for candidate in result["candidates"]] == ["agent-cheap"]
    assert result["policy_checks"] == [
        "provider_allowed",
        "capabilities_ok",
        "risk_tier_ok",
        "budget_ok",
    ]


def test_policy_gates_no_registry_candidates() -> None:
    config = {
        "spec": {
            "agent_registry": {
                "agents": [],
            }
        }
    }

    with pytest.raises(PolicyGateError) as err:
        apply_policy_gates(
            _base_request(),
            derived_metadata=_base_derived(),
            routing_config=config,
        )

    assert err.value.code == "NO_CANDIDATE_MATCH"
    assert err.value.details["gate"] == "registry"


def test_policy_budget_uses_cost_band_fallback() -> None:
    config = _base_config()
    config["spec"]["agent_registry"]["agents"] = [
        {
            "id": "agent-free",
            "provider": "github-copilot",
            "model": "github-copilot/gpt-5-mini",
            "tier": "cheap",
            "capabilities": ["implementation", "review"],
            "cost_band": "free",
        },
        {
            "id": "agent-draconic",
            "provider": "github-copilot",
            "model": "github-copilot/gpt-5.5",
            "tier": "reasoning",
            "capabilities": ["implementation", "review"],
            "cost_band": "draconic",
        },
    ]

    request = _base_request()
    request["constraints"] = {
        "provider_allowlist": ["github-copilot"],
        "max_cost_usd": 0.1,
    }

    result = apply_policy_gates(
        request,
        derived_metadata=_base_derived(),
        routing_config=config,
    )

    assert [candidate["id"] for candidate in result["candidates"]] == ["agent-free"]
