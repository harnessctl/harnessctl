"""Hard policy gate evaluation for routing candidates."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any

_TIER_RANK: dict[str, int] = {
    "cheap": 0,
    "medium": 1,
    "strong": 2,
    "reasoning": 3,
}

_CONTEXT_SIZE_TOKENS: dict[str, tuple[int, int]] = {
    "small": (4_000, 800),
    "medium": (16_000, 2_000),
    "large": (40_000, 4_000),
}


@dataclass(slots=True)
class PolicyGateError(Exception):
    """Deterministic failure raised when hard policy gates reject candidates."""

    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _normalize_capabilities(values: Any) -> set[str]:
    normalized: set[str] = set()
    for value in _as_list(values):
        if isinstance(value, str):
            capability = value.strip().lower()
            if capability:
                normalized.add(capability)
    return normalized


def _normalize_routing_derived(derived_metadata: dict[str, Any]) -> dict[str, Any]:
    if isinstance(derived_metadata.get("derived"), dict):
        return derived_metadata["derived"]
    return derived_metadata


def _coerce_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    candidate: float | None = None
    if isinstance(value, (int, float)):
        candidate = float(value)
    elif isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            candidate = float(stripped)
        except ValueError:
            return None
    if candidate is None or not math.isfinite(candidate):
        return None
    return candidate


def _risk_floor_for_task_class(config: dict[str, Any], task_class: str) -> str | None:
    spec = _as_dict(config.get("spec"))
    policies = _as_dict(spec.get("policies"))
    risk = _as_dict(policies.get("risk"))
    floors = _as_dict(risk.get("min_tier_by_task_class"))
    raw = floors.get(task_class)
    if not isinstance(raw, str):
        raw = floors.get("default")
    if not isinstance(raw, str):
        return None
    normalized = raw.strip().lower()
    return normalized if normalized in _TIER_RANK else None


def _resolve_token_estimates(
    request: dict[str, Any],
) -> tuple[float | None, float | None]:
    context = _as_dict(request.get("context"))
    in_tokens = _coerce_float(context.get("estimated_input_tokens"))
    out_tokens = _coerce_float(context.get("estimated_output_tokens"))
    if in_tokens is not None and out_tokens is not None:
        return in_tokens, out_tokens

    context_size = context.get("estimated_context_size")
    if isinstance(context_size, str):
        lookup = _CONTEXT_SIZE_TOKENS.get(context_size.strip().lower())
        if lookup is not None:
            return float(lookup[0]), float(lookup[1])
    return None, None


def _estimate_agent_cost_usd(
    agent: dict[str, Any], request: dict[str, Any]
) -> float | None:
    cost = _as_dict(agent.get("cost"))
    direct = _coerce_float(cost.get("estimated_cost_usd"))
    if direct is not None and direct >= 0:
        return direct

    input_per_1m = _coerce_float(cost.get("input_per_1m"))
    output_per_1m = _coerce_float(cost.get("output_per_1m"))
    if input_per_1m is None or output_per_1m is None:
        return None

    estimated_input, estimated_output = _resolve_token_estimates(request)
    if estimated_input is None or estimated_output is None:
        return None

    if input_per_1m < 0 or output_per_1m < 0:
        return None

    return (estimated_input / 1_000_000.0 * input_per_1m) + (
        estimated_output / 1_000_000.0 * output_per_1m
    )


def apply_policy_gates(
    request: dict[str, Any],
    *,
    derived_metadata: dict[str, Any],
    routing_config: dict[str, Any],
) -> dict[str, Any]:
    """Apply deterministic hard policy gates before scoring.

    Gate order:
    1) provider allowlist
    2) required capabilities
    3) risk tier floor
    4) budget
    5) fallback NO_CANDIDATE_MATCH
    """
    derived = _normalize_routing_derived(derived_metadata)
    task_class = str(derived.get("task_class") or "implementation").strip().lower()
    required_capabilities = _normalize_capabilities(
        derived.get("required_capabilities")
    )

    spec = _as_dict(routing_config.get("spec"))
    registry = _as_dict(spec.get("agent_registry"))
    agents = [
        agent for agent in _as_list(registry.get("agents")) if isinstance(agent, dict)
    ]
    if not agents:
        raise PolicyGateError(
            code="NO_CANDIDATE_MATCH",
            message="No agents available in registry.",
            details={"gate": "registry", "candidates_considered": 0},
        )

    policy_checks: list[str] = []
    candidates = list(agents)

    constraints = _as_dict(request.get("constraints"))
    allowlist_raw = constraints.get("provider_allowlist")
    allowlist = {
        provider.strip().lower()
        for provider in _as_list(allowlist_raw)
        if isinstance(provider, str) and provider.strip()
    }
    if allowlist:
        candidates = [
            agent
            for agent in candidates
            if str(agent.get("provider") or "").strip().lower() in allowlist
        ]
        if not candidates:
            raise PolicyGateError(
                code="PROVIDER_BLOCKED",
                message="No candidates left after provider allowlist gate.",
                details={"gate": "provider_allowlist", "allowlist": sorted(allowlist)},
            )
    policy_checks.append("provider_allowed")

    if required_capabilities:
        capability_filtered = [
            agent
            for agent in candidates
            if required_capabilities.issubset(
                _normalize_capabilities(agent.get("capabilities"))
            )
        ]
        if not capability_filtered:
            raise PolicyGateError(
                code="CAPABILITY_BLOCKED",
                message="No candidates satisfy required capabilities.",
                details={
                    "gate": "capabilities",
                    "required_capabilities": sorted(required_capabilities),
                },
            )
        candidates = capability_filtered
    policy_checks.append("capabilities_ok")

    risk_floor = _risk_floor_for_task_class(routing_config, task_class)
    if risk_floor is not None:
        floor_rank = _TIER_RANK[risk_floor]
        risk_filtered = [
            agent
            for agent in candidates
            if _TIER_RANK.get(str(agent.get("tier") or "").strip().lower(), -1)
            >= floor_rank
        ]
        if not risk_filtered:
            raise PolicyGateError(
                code="RISK_BLOCKED",
                message="No candidates satisfy minimum risk tier policy.",
                details={
                    "gate": "risk_floor",
                    "task_class": task_class,
                    "min_tier": risk_floor,
                },
            )
        candidates = risk_filtered
    policy_checks.append("risk_tier_ok")

    max_cost_usd = _coerce_float(constraints.get("max_cost_usd"))
    if max_cost_usd is not None:
        budget_filtered: list[dict[str, Any]] = []
        unknown_cost_agents: list[str] = []
        estimated_cost_by_agent: dict[str, float] = {}
        for agent in candidates:
            estimated_cost = _estimate_agent_cost_usd(agent, request)
            agent_id = str(agent.get("id") or "<unknown>")
            if estimated_cost is None:
                unknown_cost_agents.append(agent_id)
                continue
            estimated_cost_by_agent[agent_id] = estimated_cost
            if estimated_cost <= max_cost_usd:
                budget_filtered.append(agent)

        if not budget_filtered:
            raise PolicyGateError(
                code="BUDGET_BLOCKED",
                message="All valid candidates exceed budget or lack usable cost metadata.",
                details={
                    "gate": "budget",
                    "max_cost_usd": max_cost_usd,
                    "unknown_cost_agents": unknown_cost_agents,
                    "estimated_cost_by_agent": estimated_cost_by_agent,
                },
            )
        candidates = budget_filtered
    policy_checks.append("budget_ok")

    if not candidates:
        raise PolicyGateError(
            code="NO_CANDIDATE_MATCH",
            message="No candidates remain after policy gates.",
            details={"gate": "final", "policy_checks": policy_checks},
        )

    return {
        "candidates": candidates,
        "policy_checks": policy_checks,
    }
