"""Deterministic candidate scoring and primary agent selection."""

from __future__ import annotations

from typing import Any

from harnessctl.routing.policy import (
    _TIER_RANK,
    _as_dict,
    _coerce_float,
    _resolve_token_estimates,
)

_VALID_OBJECTIVES = {"cost", "cost_per_success"}


def _estimate_cost_usd(agent: dict[str, Any], request: dict[str, Any]) -> float | None:
    cost = _as_dict(agent.get("cost"))
    direct = _coerce_float(cost.get("estimated_cost_usd"))
    if direct is not None and direct >= 0:
        return direct

    input_per_1m = _coerce_float(cost.get("input_per_1m"))
    output_per_1m = _coerce_float(cost.get("output_per_1m"))
    if input_per_1m is None or output_per_1m is None:
        return None
    if input_per_1m < 0 or output_per_1m < 0:
        return None

    estimated_input, estimated_output = _resolve_token_estimates(request)
    if estimated_input is None or estimated_output is None:
        return None

    return (estimated_input / 1_000_000.0 * input_per_1m) + (
        estimated_output / 1_000_000.0 * output_per_1m
    )


def _success_probability(agent: dict[str, Any]) -> float | None:
    cost = _as_dict(agent.get("cost"))
    quality = _as_dict(agent.get("quality"))
    raw = (
        agent.get("success_probability")
        if "success_probability" in agent
        else cost.get("success_probability")
    )
    if raw is None:
        raw = quality.get("success_probability")
    value = _coerce_float(raw)
    if value is None or value <= 0 or value > 1:
        return None
    return value


def _agent_id(agent: dict[str, Any]) -> str:
    raw = agent.get("id")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return "<unknown>"


def _score_for_objective(
    *,
    objective: str,
    agent: dict[str, Any],
    request: dict[str, Any],
) -> float | None:
    estimated_cost = _estimate_cost_usd(agent, request)
    if estimated_cost is None:
        return None

    if objective == "cost":
        return estimated_cost

    success_probability = _success_probability(agent)
    if success_probability is None:
        return None
    return estimated_cost / success_probability


def _ranking_tuple(
    *,
    score: float | None,
    agent: dict[str, Any],
) -> tuple[int, float, int, str]:
    unknown_score = 1 if score is None else 0
    numeric_score = score if score is not None else float("inf")
    tier = str(agent.get("tier") or "").strip().lower()
    # Higher tier first as deterministic tiebreaker for same score.
    tier_tiebreak = -_TIER_RANK.get(tier, -1)
    return (unknown_score, numeric_score, tier_tiebreak, _agent_id(agent))


def select_primary_candidate(
    *,
    request: dict[str, Any],
    candidates: list[dict[str, Any]],
    objective: str,
) -> dict[str, Any]:
    """Score candidates deterministically and select a primary agent.

    Args:
        request: Original routing request used for token/cost estimation.
        candidates: Candidate agents already filtered by hard policy gates.
        objective: Scoring objective (`cost` or `cost_per_success`).

    Returns:
        Dict with selected candidate id, selected candidate object, and ranked list.
    """
    if not isinstance(objective, str):
        raise ValueError(
            "Unsupported scoring objective. Expected one of: cost, cost_per_success"
        )

    normalized_objective = objective.strip().lower()
    if normalized_objective not in _VALID_OBJECTIVES:
        raise ValueError(
            "Unsupported scoring objective. Expected one of: cost, cost_per_success"
        )
    if not candidates:
        raise ValueError("Cannot select a primary candidate from an empty list.")

    ranked_rows: list[dict[str, Any]] = []
    for agent in candidates:
        if not isinstance(agent, dict):
            continue
        score = _score_for_objective(
            objective=normalized_objective,
            agent=agent,
            request=request,
        )
        ranked_rows.append(
            {
                "agent": agent,
                "agent_id": _agent_id(agent),
                "score": score,
                "rank_key": _ranking_tuple(score=score, agent=agent),
            }
        )

    if not ranked_rows:
        raise ValueError("No dictionary-based candidate agents were provided.")

    ranked_rows.sort(key=lambda row: row["rank_key"])
    selected = ranked_rows[0]

    return {
        "objective": normalized_objective,
        "selection_strategy": f"deterministic_{normalized_objective}",
        "selected_agent_id": selected["agent_id"],
        "selected_agent": selected["agent"],
        "ranked_candidates": [
            {
                "agent_id": row["agent_id"],
                "score": row["score"],
            }
            for row in ranked_rows
        ],
    }
