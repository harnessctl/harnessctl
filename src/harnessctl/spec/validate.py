"""Semantic validation for harnessctl specs."""

from harnessctl.spec.models import Spec
from harnessctl.spec.warnings import WarningCollector


class SpecError(Exception):
    """Raised when the spec fails semantic validation."""

    pass


def validate_references(spec: Spec, warnings: WarningCollector) -> None:
    """Validate cross-references inside *spec* and emit warnings where appropriate.

    Raises:
        SpecError: When a required reference is missing or a duplicate scope name
            is detected within a harness target.
    """
    _validate_agents(spec)
    _validate_tiers(spec)
    _validate_profiles(spec)
    _validate_harness_scopes(spec, warnings)


def _validate_agents(spec: Spec) -> None:
    for agent_id, agent in spec.agents.items():
        if agent.tier not in spec.tiers:
            raise SpecError(
                f"Agent '{agent_id}' references unknown tier '{agent.tier}'."
            )


def _validate_tiers(spec: Spec) -> None:
    for tier_id, tier in spec.tiers.items():
        if tier.primary not in spec.models:
            raise SpecError(
                f"Tier '{tier_id}' primary model '{tier.primary}' not found in models."
            )
        if tier.fallback is not None and tier.fallback not in spec.models:
            raise SpecError(
                f"Tier '{tier_id}' fallback model '{tier.fallback}' not found in models."
            )


def _validate_profiles(spec: Spec) -> None:
    for profile_id, profile in spec.profiles.items():
        if (
            profile.preferred_tier is not None
            and profile.preferred_tier not in spec.tiers
        ):
            raise SpecError(
                f"Profile '{profile_id}' preferred_tier '{profile.preferred_tier}' not found in tiers."
            )


def _validate_harness_scopes(spec: Spec, warnings: WarningCollector) -> None:
    for harness_id, target in spec.harness.items():
        seen_names: set[str] = set()
        for scope in target.scopes:
            if scope.name in seen_names:
                raise SpecError(
                    f"Harness '{harness_id}' contains duplicate scope name '{scope.name}'."
                )
            seen_names.add(scope.name)

            if scope.kind == "custom" and scope.launch_env is None:
                warnings.add(
                    field="scopes",
                    reason="Custom scope lacks launch_env, will be inert",
                    harness=harness_id,
                )
