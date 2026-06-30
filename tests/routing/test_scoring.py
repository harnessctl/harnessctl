"""Tests for deterministic routing candidate scoring and selection."""

from __future__ import annotations

import pytest

from harnessctl.routing import select_primary_candidate


def _request() -> dict[str, object]:
    return {
        "prompt": "Implement endpoint",
        "context": {"estimated_context_size": "medium"},
    }


def test_deterministic_repeated_selection_is_stable() -> None:
    request = _request()
    candidates = [
        {
            "id": "agent-z",
            "tier": "medium",
            "cost": {"estimated_cost_usd": 0.20},
        },
        {
            "id": "agent-a",
            "tier": "medium",
            "cost": {"estimated_cost_usd": 0.20},
        },
    ]

    first = select_primary_candidate(
        request=request,
        candidates=candidates,
        objective="cost",
    )
    second = select_primary_candidate(
        request=request,
        candidates=candidates,
        objective="cost",
    )

    assert first["selected_agent_id"] == "agent-a"
    assert second["selected_agent_id"] == "agent-a"
    assert first["ranked_candidates"] == second["ranked_candidates"]


def test_cost_objective_selects_lower_estimated_cost() -> None:
    result = select_primary_candidate(
        request=_request(),
        candidates=[
            {
                "id": "expensive",
                "tier": "reasoning",
                "cost": {"estimated_cost_usd": 0.40},
            },
            {
                "id": "cheap",
                "tier": "cheap",
                "cost": {"estimated_cost_usd": 0.05},
            },
        ],
        objective="cost",
    )

    assert result["selected_agent_id"] == "cheap"


def test_cost_per_success_can_prefer_higher_cost_better_success() -> None:
    result = select_primary_candidate(
        request=_request(),
        candidates=[
            {
                "id": "cheap-but-fragile",
                "tier": "cheap",
                "cost": {
                    "estimated_cost_usd": 0.10,
                    "success_probability": 0.20,
                },
            },
            {
                "id": "costly-but-reliable",
                "tier": "strong",
                "cost": {
                    "estimated_cost_usd": 0.20,
                    "success_probability": 0.80,
                },
            },
        ],
        objective="cost_per_success",
    )

    # 0.10/0.20 = 0.50, 0.20/0.80 = 0.25 -> second wins
    assert result["selected_agent_id"] == "costly-but-reliable"


def test_tie_break_prefers_higher_tier_then_agent_id() -> None:
    result = select_primary_candidate(
        request=_request(),
        candidates=[
            {
                "id": "medium-a",
                "tier": "medium",
                "cost": {"estimated_cost_usd": 0.10},
            },
            {
                "id": "strong-z",
                "tier": "strong",
                "cost": {"estimated_cost_usd": 0.10},
            },
            {
                "id": "strong-a",
                "tier": "strong",
                "cost": {"estimated_cost_usd": 0.10},
            },
        ],
        objective="cost",
    )

    assert result["selected_agent_id"] == "strong-a"


def test_unknown_scores_sorted_last() -> None:
    result = select_primary_candidate(
        request=_request(),
        candidates=[
            {
                "id": "unknown-cost",
                "tier": "reasoning",
                "cost": {},
            },
            {
                "id": "known-cost",
                "tier": "cheap",
                "cost": {"estimated_cost_usd": 0.20},
            },
        ],
        objective="cost",
    )

    ranked = result["ranked_candidates"]
    assert ranked[0]["agent_id"] == "known-cost"
    assert ranked[1]["agent_id"] == "unknown-cost"


def test_non_string_objective_returns_value_error() -> None:
    with pytest.raises(ValueError, match="Unsupported scoring objective"):
        select_primary_candidate(
            request=_request(),
            candidates=[
                {"id": "a", "tier": "medium", "cost": {"estimated_cost_usd": 0.2}}
            ],
            objective=123,  # type: ignore[arg-type]
        )


def test_non_finite_cost_is_treated_as_unknown() -> None:
    result = select_primary_candidate(
        request=_request(),
        candidates=[
            {
                "id": "nan-cost",
                "tier": "reasoning",
                "cost": {"estimated_cost_usd": "nan"},
            },
            {
                "id": "known-cost",
                "tier": "cheap",
                "cost": {"estimated_cost_usd": 0.2},
            },
        ],
        objective="cost",
    )

    ranked = result["ranked_candidates"]
    assert ranked[0]["agent_id"] == "known-cost"
    assert ranked[1]["agent_id"] == "nan-cost"


def test_cost_band_fallback_is_used_for_cost_objective() -> None:
    result = select_primary_candidate(
        request=_request(),
        candidates=[
            {
                "id": "draconic-agent",
                "tier": "reasoning",
                "cost_band": "draconic",
            },
            {
                "id": "free-agent",
                "tier": "cheap",
                "cost_band": "free",
            },
        ],
        objective="cost",
    )

    assert result["selected_agent_id"] == "free-agent"
