"""Deterministic escalation and fallback-chain selection helpers."""

from __future__ import annotations

from typing import Any

from harnessctl.routing.policy import _TIER_RANK, _as_dict, _as_list


_VALID_FAILURE_ACTIONS = {
    "retry_same_tier",
    "retry_with_stricter_prompt",
    "retry_same_tier_then_escalate",
    "escalate_next_tier",
    "escalate_to_reasoning",
    "escalate_or_stop",
}


def _normalize_derived(derived_metadata: dict[str, Any]) -> dict[str, Any]:
    derived = derived_metadata.get("derived")
    if isinstance(derived, dict):
        return derived
    return derived_metadata


def _normalize_tiers(raw: Any) -> list[str]:
    tiers: list[str] = []
    for value in _as_list(raw):
        if not isinstance(value, str):
            continue
        tier = value.strip().lower()
        if tier in _TIER_RANK and tier not in tiers:
            tiers.append(tier)
    return tiers


def _chains_by_name(escalation: dict[str, Any]) -> dict[str, list[str]]:
    chains: dict[str, list[str]] = {}
    for entry in _as_list(escalation.get("chains")):
        if not isinstance(entry, dict):
            continue
        raw_name = entry.get("name")
        if not isinstance(raw_name, str) or not raw_name.strip():
            continue
        name = raw_name.strip().lower()
        tiers = _normalize_tiers(entry.get("tiers") or entry.get("steps"))
        if tiers:
            chains[name] = tiers
    return chains


def _matched_keyword_override(
    *,
    prompt: str,
    escalation: dict[str, Any],
) -> tuple[str | None, str | None]:
    lowered_prompt = prompt.lower()
    for entry in _as_list(escalation.get("keyword_overrides")):
        if not isinstance(entry, dict):
            continue
        use_chain = entry.get("use_chain")
        if not isinstance(use_chain, str) or not use_chain.strip():
            continue
        chain_name = use_chain.strip().lower()
        for keyword in _as_list(entry.get("match_any")):
            if not isinstance(keyword, str):
                continue
            normalized = keyword.strip().lower()
            if normalized and normalized in lowered_prompt:
                raw_name = entry.get("name")
                override_name = raw_name.strip() if isinstance(raw_name, str) else None
                return chain_name, override_name
    return None, None


def _resolve_failure_action(
    *,
    request: dict[str, Any],
    escalation: dict[str, Any],
    explicit_failure_kind: str | None,
) -> tuple[str, str | None]:
    failure_kind = None
    if isinstance(explicit_failure_kind, str) and explicit_failure_kind.strip():
        failure_kind = explicit_failure_kind.strip().lower()
    if failure_kind is None:
        context = _as_dict(request.get("context"))
        hint_map = _as_dict(request.get("hints"))
        failure_hint = context.get("failure_kind") or hint_map.get("failure_kind")
        if isinstance(failure_hint, str) and failure_hint.strip():
            failure_kind = failure_hint.strip().lower()

    failure_policies = _as_dict(escalation.get("failure_policies"))
    if failure_kind and failure_kind in failure_policies:
        entry = _as_dict(failure_policies.get(failure_kind))
        action = entry.get("action")
        if isinstance(action, str) and action.strip().lower() in _VALID_FAILURE_ACTIONS:
            return action.strip().lower(), failure_kind

    return "retry_same_tier_then_escalate", failure_kind


def _tier_sequence_for_action(
    *,
    base_tiers: list[str],
    selected_tier: str | None,
    action: str,
) -> list[str]:
    if not base_tiers:
        return []

    if action == "escalate_or_stop":
        return []

    if action == "escalate_to_reasoning":
        return ["reasoning"] if "reasoning" in base_tiers else []

    if selected_tier is None or selected_tier not in base_tiers:
        return list(base_tiers)

    selected_index = base_tiers.index(selected_tier)

    if action == "escalate_next_tier":
        return base_tiers[selected_index + 1 :]

    if action in {"retry_same_tier", "retry_with_stricter_prompt"}:
        return [selected_tier]

    return [selected_tier, *base_tiers[selected_index + 1 :]]


def _sorted_agent_ids_for_tiers(
    *,
    candidates: list[dict[str, Any]],
    tier_sequence: list[str],
    selected_agent_id: str,
) -> list[str]:
    ids: list[str] = []
    for tier in tier_sequence:
        tier_ids = sorted(
            str(agent.get("id") or "").strip()
            for agent in candidates
            if str(agent.get("tier") or "").strip().lower() == tier
            and str(agent.get("id") or "").strip()
            and str(agent.get("id") or "").strip() != selected_agent_id
        )
        ids.extend(tier_ids)
    return ids


def build_fallback_chain(
    *,
    request: dict[str, Any],
    derived_metadata: dict[str, Any],
    routing_config: dict[str, Any],
    candidates: list[dict[str, Any]],
    selected_agent_id: str,
    failure_kind: str | None = None,
) -> dict[str, Any]:
    """Build deterministic fallback agent chain from escalation policy.

    Chain selection order:
    1. keyword override chain (first match)
    2. strategy-keyed chain (default task_class)
    3. fallback-on-unknown chain
    4. built-in `default` chain
    """
    derived = _normalize_derived(derived_metadata)
    task_class = str(derived.get("task_class") or "implementation").strip().lower()
    prompt = str(request.get("prompt") or "")

    spec = _as_dict(routing_config.get("spec"))
    escalation = _as_dict(spec.get("escalation"))
    strategy = _as_dict(escalation.get("strategy"))

    chains = _chains_by_name(escalation)
    if not chains:
        return {
            "chain_name": "default",
            "fallback_agents": [],
            "tier_sequence": [],
            "escalation_action": "retry_same_tier_then_escalate",
            "matched_keyword_override": None,
            "failure_kind": failure_kind,
        }

    override_chain, override_name = _matched_keyword_override(
        prompt=prompt,
        escalation=escalation,
    )

    fallback_unknown = str(strategy.get("fallback_on_unknown_task_class") or "default")
    fallback_unknown = fallback_unknown.strip().lower()

    keying = str(strategy.get("keying") or "task_class").strip().lower()
    chain_key = task_class
    if keying == "manual":
        manual_chain = _as_dict(request.get("hints")).get("escalation_chain")
        if not isinstance(manual_chain, str):
            manual_chain = _as_dict(request.get("constraints")).get("escalation_chain")
        if isinstance(manual_chain, str) and manual_chain.strip():
            chain_key = manual_chain.strip().lower()

    resolved_chain = override_chain or chain_key
    if resolved_chain not in chains:
        resolved_chain = fallback_unknown if fallback_unknown in chains else "default"
    if resolved_chain not in chains:
        resolved_chain = sorted(chains.keys())[0]

    base_tiers = chains[resolved_chain]
    action, resolved_failure_kind = _resolve_failure_action(
        request=request,
        escalation=escalation,
        explicit_failure_kind=failure_kind,
    )

    selected_tier = None
    for agent in candidates:
        agent_id = str(agent.get("id") or "").strip()
        if agent_id == selected_agent_id:
            tier = str(agent.get("tier") or "").strip().lower()
            selected_tier = tier if tier in _TIER_RANK else None
            break

    tier_sequence = _tier_sequence_for_action(
        base_tiers=base_tiers,
        selected_tier=selected_tier,
        action=action,
    )

    fallback_agents = _sorted_agent_ids_for_tiers(
        candidates=candidates,
        tier_sequence=tier_sequence,
        selected_agent_id=selected_agent_id,
    )

    return {
        "chain_name": resolved_chain,
        "fallback_agents": fallback_agents,
        "tier_sequence": tier_sequence,
        "escalation_action": action,
        "matched_keyword_override": override_name,
        "failure_kind": resolved_failure_kind,
    }
