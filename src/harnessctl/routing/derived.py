"""Derive routing metadata and provenance from minimally-specified requests."""

from __future__ import annotations

import math
import re
from typing import Any

_DEFAULT_TASK_CLASS = "implementation"

_TASK_CLASS_CAPABILITIES: dict[str, list[str]] = {
    "hld": ["design", "reasoning"],
    "lld": ["design", "reasoning"],
    "architecture": ["design", "reasoning"],
    "security": ["security_analysis", "reasoning"],
    "backend": ["implementation", "review"],
    "frontend": ["implementation", "review"],
    "gaming": ["implementation", "reasoning"],
    "debugging": ["implementation", "reasoning"],
    "performance": ["implementation", "reasoning"],
    "docs": ["docs", "review"],
    "review": ["review"],
    "implementation": ["implementation", "review"],
}

_RISK_BY_TASK_CLASS: dict[str, str] = {
    "security": "high",
    "architecture": "high",
    "hld": "high",
    "lld": "medium",
    "migration": "medium",
    "performance": "medium",
    "debugging": "medium",
}

_CLASS_KEYWORDS: dict[str, tuple[str, ...]] = {
    "hld": ("hld", "high level design", "high-level design"),
    "lld": ("lld", "low level design", "low-level design"),
    "security": ("auth", "permission", "token", "secret", "sandbox"),
    "architecture": (
        "architecture",
        "distributed",
        "consistency",
        "concurrency",
        "event sourcing",
    ),
    "gaming": ("gameplay", "godot", "shader", "physics"),
    "frontend": ("frontend", "ui", "ux", "component"),
    "backend": ("backend", "api", "database", "service"),
    "debugging": ("debug", "fix", "failing", "error", "traceback"),
    "performance": ("optimize", "performance", "latency", "throughput"),
    "docs": ("docs", "documentation", "readme"),
}

_COMPLEXITY_WEIGHTS: dict[str, int] = {
    "distributed": 20,
    "architecture": 20,
    "security": 20,
    "migration": 15,
    "performance": 15,
    "debug": 10,
    "refactor": 10,
    "test": 8,
}


def _coerce_str(value: Any) -> str | None:
    """Return a trimmed string value, or ``None`` when blank/non-string."""
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped if stripped else None


def _taxonomy_aliases(config: dict[str, Any] | None) -> dict[str, str]:
    """Extract normalized taxonomy aliases from routing config."""
    if not isinstance(config, dict):
        return {}
    spec = config.get("spec")
    if not isinstance(spec, dict):
        return {}
    taxonomy = spec.get("taxonomy")
    if not isinstance(taxonomy, dict):
        return {}
    aliases = taxonomy.get("aliases")
    if not isinstance(aliases, dict):
        return {}

    normalized: dict[str, str] = {}
    for alias, target in aliases.items():
        alias_value = _coerce_str(alias)
        target_value = _coerce_str(target)
        if alias_value is None or target_value is None:
            continue
        normalized[alias_value.lower()] = target_value.lower()
    return normalized


def _normalize_task_class(
    value: str | None, aliases: dict[str, str]
) -> tuple[str, str | None]:
    """Normalize task class and resolve alias mappings when present."""
    if value is None:
        return _DEFAULT_TASK_CLASS, None

    lowered = value.lower()
    if lowered in aliases:
        return aliases[lowered], "alias"
    return lowered, None


def _infer_task_class_from_prompt(prompt: str) -> str:
    """Infer task class from prompt keywords using boundary-aware matching."""
    lowered = prompt.lower()
    for task_class, keywords in _CLASS_KEYWORDS.items():
        if any(_keyword_match(lowered, keyword) for keyword in keywords):
            return task_class
    return _DEFAULT_TASK_CLASS


def _keyword_match(text: str, keyword: str) -> bool:
    """Return True when keyword appears as a standalone token sequence."""
    normalized_keyword = keyword.strip().lower()
    if not normalized_keyword:
        return False
    parts = [re.escape(part) for part in normalized_keyword.split() if part]
    if not parts:
        return False
    pattern = r"\b" + r"\s+".join(parts) + r"\b"
    return re.search(pattern, text) is not None


def _infer_risk(task_class: str, prompt: str) -> str:
    """Infer risk level from task class, escalating on security signal words."""
    lowered = prompt.lower()
    if any(keyword in lowered for keyword in _CLASS_KEYWORDS.get("security", ())):
        return "high"
    return _RISK_BY_TASK_CLASS.get(task_class, "low")


def _infer_complexity(prompt: str) -> int:
    """Infer complexity score (0-100) from weighted keywords and prompt size."""
    lowered = prompt.lower()
    score = 15
    for keyword, weight in _COMPLEXITY_WEIGHTS.items():
        if keyword in lowered:
            score += weight

    word_count = len([word for word in lowered.split() if word])
    if word_count > 20:
        score += 10
    if word_count > 40:
        score += 10

    return max(0, min(100, score))


def _coerce_complexity(value: Any) -> int | None:
    """Coerce complexity hint to bounded integer, or return ``None`` if invalid."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return max(0, min(100, value))
    if isinstance(value, float):
        return max(0, min(100, int(value)))
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            parsed_float = float(stripped)
            if not math.isfinite(parsed_float):
                return None
            parsed = int(parsed_float)
        except (OverflowError, ValueError):
            return None
        return max(0, min(100, parsed))
    return None


def _unique_preserve_order(values: list[str]) -> list[str]:
    """Deduplicate values while preserving first-seen order."""
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def derive_task_metadata(
    request: dict[str, Any],
    *,
    routing_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Derive routing metadata and field-level provenance.

    Returns an object with:
    - ``derived``: normalized derived metadata used by routing
    - ``provenance``: source labels per derived field
    """
    prompt = _coerce_str(request.get("prompt")) or ""
    task_type = _coerce_str(request.get("task_type"))

    hints = request.get("hints")
    hints_map = hints if isinstance(hints, dict) else {}

    constraints = request.get("constraints")
    constraints_map = constraints if isinstance(constraints, dict) else {}

    aliases = _taxonomy_aliases(routing_config)

    if task_type is not None:
        task_class, alias_source = _normalize_task_class(task_type, aliases)
        task_class_provenance = "caller_hint"
        if alias_source is not None:
            task_class_provenance = "caller_hint_alias"
    else:
        inferred_class = _infer_task_class_from_prompt(prompt)
        task_class, _ = _normalize_task_class(inferred_class, aliases)
        task_class_provenance = "inferred"

    inferred_capabilities = list(
        _TASK_CLASS_CAPABILITIES.get(
            task_class, _TASK_CLASS_CAPABILITIES[_DEFAULT_TASK_CLASS]
        )
    )
    user_required_raw = constraints_map.get("user_required_capabilities")
    user_required = (
        [
            capability.strip().lower()
            for capability in user_required_raw
            if isinstance(capability, str) and capability.strip()
        ]
        if isinstance(user_required_raw, list)
        else []
    )

    required_capabilities = _unique_preserve_order(
        inferred_capabilities + user_required
    )
    required_capabilities_provenance = (
        "inferred+user_add" if user_required else "inferred"
    )

    hint_risk = _coerce_str(hints_map.get("risk"))
    if hint_risk is not None:
        risk = hint_risk.lower()
        risk_provenance = "caller_hint"
    else:
        risk = _infer_risk(task_class, prompt)
        risk_provenance = "inferred"

    hint_complexity = _coerce_complexity(hints_map.get("complexity"))
    if hint_complexity is not None:
        complexity = hint_complexity
        complexity_provenance = "caller_hint"
    else:
        complexity = _infer_complexity(prompt)
        complexity_provenance = "inferred"

    return {
        "derived": {
            "task_class": task_class,
            "required_capabilities": required_capabilities,
            "risk": risk,
            "complexity": complexity,
        },
        "provenance": {
            "task_class": task_class_provenance,
            "required_capabilities": required_capabilities_provenance,
            "risk": risk_provenance,
            "complexity": complexity_provenance,
        },
    }
