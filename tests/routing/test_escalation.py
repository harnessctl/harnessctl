from harnessctl.routing import build_fallback_chain


def _routing_config() -> dict:
    return {
        "spec": {
            "escalation": {
                "strategy": {
                    "keying": "task_class",
                    "fallback_on_unknown_task_class": "default",
                },
                "chains": [
                    {"name": "default", "tiers": ["cheap", "medium", "strong"]},
                    {"name": "frontend", "tiers": ["cheap", "medium", "strong"]},
                    {"name": "security", "tiers": ["strong", "reasoning"]},
                    {"name": "gaming", "tiers": ["medium", "strong", "reasoning"]},
                ],
                "keyword_overrides": [
                    {
                        "name": "gameplay-terms",
                        "match_any": ["godot", "shader", "gameplay"],
                        "use_chain": "gaming",
                    }
                ],
                "failure_policies": {
                    "wrong_solution": {"action": "escalate_next_tier"},
                    "security_risk": {"action": "escalate_to_reasoning"},
                },
            }
        }
    }


def _candidates() -> list[dict]:
    return [
        {"id": "agent-a", "tier": "cheap"},
        {"id": "agent-b", "tier": "medium"},
        {"id": "agent-c", "tier": "strong"},
        {"id": "agent-d", "tier": "reasoning"},
    ]


def test_task_class_selects_matching_chain() -> None:
    result = build_fallback_chain(
        request={"prompt": "Build UI component"},
        derived_metadata={"derived": {"task_class": "frontend"}},
        routing_config=_routing_config(),
        candidates=_candidates(),
        selected_agent_id="agent-a",
    )

    assert result["chain_name"] == "frontend"
    assert result["tier_sequence"] == ["cheap", "medium", "strong"]
    assert result["fallback_agents"] == ["agent-b", "agent-c"]


def test_keyword_override_can_change_chain() -> None:
    result = build_fallback_chain(
        request={"prompt": "Need godot shader optimization"},
        derived_metadata={"derived": {"task_class": "frontend"}},
        routing_config=_routing_config(),
        candidates=_candidates(),
        selected_agent_id="agent-b",
    )

    assert result["chain_name"] == "gaming"
    assert result["matched_keyword_override"] == "gameplay-terms"
    assert result["fallback_agents"] == ["agent-c", "agent-d"]


def test_failure_policy_can_force_reasoning_only_chain() -> None:
    result = build_fallback_chain(
        request={"prompt": "security review"},
        derived_metadata={"derived": {"task_class": "security"}},
        routing_config=_routing_config(),
        candidates=_candidates(),
        selected_agent_id="agent-c",
        failure_kind="security_risk",
    )

    assert result["chain_name"] == "security"
    assert result["escalation_action"] == "escalate_to_reasoning"
    assert result["tier_sequence"] == ["reasoning"]
    assert result["fallback_agents"] == ["agent-d"]


def test_fallback_chain_is_deterministic_for_same_inputs() -> None:
    kwargs = {
        "request": {"prompt": "frontend build"},
        "derived_metadata": {"derived": {"task_class": "frontend"}},
        "routing_config": _routing_config(),
        "candidates": _candidates(),
        "selected_agent_id": "agent-a",
        "failure_kind": "wrong_solution",
    }

    first = build_fallback_chain(**kwargs)
    second = build_fallback_chain(**kwargs)
    assert first == second
