"""Tests for harnessctl.spec.validate."""

import pytest

from harnessctl.spec.models import (
    Agent,
    AgentRole,
    HarnessCapabilities,
    HarnessScope,
    HarnessTarget,
    Model,
    Profile,
    ScopeKind,
    Spec,
    Tier,
)
from harnessctl.spec.validate import SpecError, validate_references
from harnessctl.spec.warnings import WarningCollector


class TestValidateReferences:
    def test_valid_spec_passes(self) -> None:
        spec = Spec(
            version="1.0",
            tiers={
                "basic": Tier(primary="m1", fallback="m2"),
            },
            models={
                "m1": Model(),
                "m2": Model(),
            },
            agents={
                "a1": Agent(tier="basic", role=AgentRole.HUB),
            },
            profiles={
                "p1": Profile(preferred_tier="basic"),
            },
            harness={
                "h1": HarnessTarget(
                    capabilities=HarnessCapabilities(),
                    scopes=[
                        HarnessScope(name="s1", kind=ScopeKind.GLOBAL, path="/"),
                    ],
                ),
            },
        )
        warnings = WarningCollector()
        validate_references(spec, warnings)
        assert not warnings.has_warnings()

    def test_agent_tier_missing_raises(self) -> None:
        spec = Spec(
            agents={"a1": Agent(tier="missing", role=AgentRole.HUB)},
        )
        with pytest.raises(SpecError, match="unknown tier 'missing'"):
            validate_references(spec, WarningCollector())

    def test_tier_primary_missing_raises(self) -> None:
        spec = Spec(
            tiers={"basic": Tier(primary="missing")},
        )
        with pytest.raises(SpecError, match="primary model 'missing' not found"):
            validate_references(spec, WarningCollector())

    def test_tier_fallback_missing_raises(self) -> None:
        spec = Spec(
            tiers={"basic": Tier(primary="m1", fallback="missing")},
            models={"m1": Model()},
        )
        with pytest.raises(SpecError, match="fallback model 'missing' not found"):
            validate_references(spec, WarningCollector())

    def test_profile_preferred_tier_missing_raises(self) -> None:
        spec = Spec(
            profiles={"p1": Profile(preferred_tier="missing")},
        )
        with pytest.raises(SpecError, match="preferred_tier 'missing' not found"):
            validate_references(spec, WarningCollector())

    def test_duplicate_scope_name_raises(self) -> None:
        spec = Spec(
            harness={
                "h1": HarnessTarget(
                    capabilities=HarnessCapabilities(),
                    scopes=[
                        HarnessScope(name="s1", kind=ScopeKind.GLOBAL, path="/"),
                        HarnessScope(name="s1", kind=ScopeKind.PROJECT, path="/p"),
                    ],
                ),
            },
        )
        with pytest.raises(SpecError, match="duplicate scope name 's1'"):
            validate_references(spec, WarningCollector())

    def test_custom_scope_without_launch_env_warns(self) -> None:
        spec = Spec(
            harness={
                "h1": HarnessTarget(
                    capabilities=HarnessCapabilities(),
                    scopes=[
                        HarnessScope(
                            name="c1",
                            kind=ScopeKind.CUSTOM,
                            path="/custom",
                            launch_env=None,
                        ),
                    ],
                ),
            },
        )
        warnings = WarningCollector()
        validate_references(spec, warnings)
        assert warnings.has_warnings()
        assert len(warnings.warnings) == 1
        w = warnings.warnings[0]
        assert w.harness == "h1"
        assert w.field == "scopes"
        assert "launch_env" in w.reason

    def test_custom_scope_with_launch_env_no_warning(self) -> None:
        spec = Spec(
            harness={
                "h1": HarnessTarget(
                    capabilities=HarnessCapabilities(),
                    scopes=[
                        HarnessScope(
                            name="c1",
                            kind=ScopeKind.CUSTOM,
                            path="/custom",
                            launch_env={"KEY": "val"},
                        ),
                    ],
                ),
            },
        )
        warnings = WarningCollector()
        validate_references(spec, warnings)
        assert not warnings.has_warnings()

    def test_multiple_harnesses_validated(self) -> None:
        spec = Spec(
            harness={
                "h1": HarnessTarget(
                    capabilities=HarnessCapabilities(),
                    scopes=[
                        HarnessScope(name="s1", kind=ScopeKind.GLOBAL, path="/"),
                    ],
                ),
                "h2": HarnessTarget(
                    capabilities=HarnessCapabilities(),
                    scopes=[
                        HarnessScope(name="s1", kind=ScopeKind.GLOBAL, path="/"),
                        HarnessScope(name="s2", kind=ScopeKind.CUSTOM, path="/c"),
                    ],
                ),
            },
        )
        warnings = WarningCollector()
        validate_references(spec, warnings)
        assert warnings.has_warnings()
        assert len(warnings.warnings) == 1
        assert warnings.warnings[0].harness == "h2"
