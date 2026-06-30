"""Provider preset loading helpers for config bootstrap."""

from __future__ import annotations

from importlib import resources
from typing import Any

import yaml

SUPPORTED_PROVIDERS: tuple[str, ...] = ("github-copilot", "openrouter")


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _preset_resource_name(provider: str) -> str:
    return f"{provider}.yaml"


def load_provider_preset(provider: str) -> dict[str, Any]:
    """Load packaged provider preset YAML by provider identifier."""
    if provider not in SUPPORTED_PROVIDERS:
        supported = ", ".join(SUPPORTED_PROVIDERS)
        raise ValueError(f"Unsupported provider: {provider!r}. Supported: {supported}")

    resource = resources.files("harnessctl.config.presets") / _preset_resource_name(
        provider
    )
    with resource.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)

    if not isinstance(loaded, dict):
        raise ValueError(f"Invalid preset format for provider {provider!r}")
    return loaded


def build_routing_config_from_preset(provider: str) -> dict[str, Any]:
    """Build starter routing config using defaults from a provider preset."""
    preset = load_provider_preset(provider)
    spec = preset.get("spec")
    if not isinstance(spec, dict):
        raise ValueError(f"Invalid preset spec for provider {provider!r}")

    defaults = spec.get("defaults")
    if not isinstance(defaults, dict):
        raise ValueError(f"Invalid preset defaults for provider {provider!r}")

    agents = defaults.get("agents")
    if not isinstance(agents, list):
        raise ValueError(f"Invalid preset agents for provider {provider!r}")

    taxonomy = _as_dict(defaults.get("taxonomy"))
    task_classes = taxonomy.get("task_classes")
    aliases = taxonomy.get("aliases")
    if not isinstance(task_classes, list) or not task_classes:
        task_classes = ["implementation", "review", "docs"]
    if not isinstance(aliases, dict):
        aliases = {}

    routing_rules = _as_list_of_dicts(defaults.get("routing_rules"))
    if not routing_rules:
        routing_rules = [
            {
                "name": "default-rule",
                "when": {"task_type_in": ["implementation", "review", "docs"]},
                "choose": {
                    "preferred_tiers": ["cheap", "medium", "strong"],
                    "optimize_for": "cost",
                },
            }
        ]

    escalation = _as_dict(defaults.get("escalation"))
    if not escalation:
        escalation = {
            "strategy": {
                "keying": "task_class",
                "fallback_on_unknown_task_class": "default",
            },
            "chains": [
                {
                    "name": "default",
                    "tiers": ["cheap", "medium", "strong"],
                }
            ],
        }

    policies = _as_dict(defaults.get("policies"))

    spec: dict[str, Any] = {
        "taxonomy": {
            "task_classes": task_classes,
            "aliases": aliases,
        },
        "agent_registry": {
            "agents": agents,
        },
        "routing": {
            "rules": routing_rules,
        },
        "escalation": escalation,
        "provider_presets": [provider],
    }
    if policies:
        spec["policies"] = policies

    return {
        "apiVersion": "harnessctl/v1alpha1",
        "kind": "RoutingConfig",
        "metadata": {"name": "default"},
        "spec": spec,
    }


def build_provider_reference_from_preset(provider: str) -> dict[str, Any]:
    """Build provider reference document for config bootstrap output."""
    preset = load_provider_preset(provider)
    metadata = preset.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError(f"Invalid preset metadata for provider {provider!r}")

    name = metadata.get("name")
    if not isinstance(name, str) or not name:
        raise ValueError(f"Invalid preset metadata.name for provider {provider!r}")

    return {
        "apiVersion": "harnessctl/v1alpha1",
        "kind": "ProviderPresetReference",
        "metadata": {"name": name},
        "spec": {
            "provider": provider,
            "source": "builtin",
        },
    }
