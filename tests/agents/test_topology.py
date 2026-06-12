import pytest
from harnessctl.spec.models import Spec, Agent, Tier, AgentRole
from harnessctl.agents.topology import validate_topology, TopologyError


def test_validate_topology_valid_hub_and_spoke():
    spec = Spec(
        tiers={"balanced": Tier(primary="gpt-4"), "cheap": Tier(primary="gpt-3.5")},
        agents={
            "orchestrator": Agent(
                tier="balanced", role=AgentRole.HUB, can_delegate=["worker1", "worker2"]
            ),
            "worker1": Agent(tier="cheap", role=AgentRole.WORKER),
            "worker2": Agent(
                tier="cheap", role=AgentRole.WORKER, escalates_to="orchestrator"
            ),
        },
    )
    # Should not raise
    validate_topology(spec)


def test_validate_topology_no_hub():
    spec = Spec(
        tiers={"cheap": Tier(primary="gpt-3.5")},
        agents={"worker": Agent(tier="cheap", role=AgentRole.WORKER)},
    )
    with pytest.raises(
        TopologyError, match="Exactly one hub agent must be defined, found 0"
    ):
        validate_topology(spec)


def test_validate_topology_multiple_hubs():
    spec = Spec(
        tiers={"balanced": Tier(primary="gpt-4")},
        agents={
            "hub1": Agent(tier="balanced", role=AgentRole.HUB),
            "hub2": Agent(tier="balanced", role=AgentRole.HUB),
        },
    )
    with pytest.raises(
        TopologyError, match="Exactly one hub agent must be defined, found 2"
    ):
        validate_topology(spec)


def test_validate_topology_worker_delegate_without_cli():
    spec = Spec(
        tiers={"balanced": Tier(primary="gpt-4"), "cheap": Tier(primary="gpt-3.5")},
        agents={
            "hub": Agent(tier="balanced", role=AgentRole.HUB, can_delegate=["mid"]),
            "mid": Agent(
                tier="balanced", role=AgentRole.WORKER, can_delegate=["coder"]
            ),
            "coder": Agent(tier="cheap", role=AgentRole.WORKER),
        },
    )
    with pytest.raises(
        TopologyError,
        match=r"mid' \(worker\) cannot delegate to 'coder' using 'harness'",
    ):
        validate_topology(spec)


def test_validate_topology_worker_delegate_with_cli():
    spec = Spec(
        tiers={"balanced": Tier(primary="gpt-4"), "cheap": Tier(primary="gpt-3.5")},
        agents={
            "hub": Agent(tier="balanced", role=AgentRole.HUB, can_delegate=["mid"]),
            "mid": Agent(
                tier="balanced",
                role=AgentRole.WORKER,
                can_delegate=["coder"],
                delegate_via="cli",
            ),
            "coder": Agent(tier="cheap", role=AgentRole.WORKER),
        },
    )
    # Should not raise because delegate_via is cli
    validate_topology(spec)


def test_validate_topology_cycle():
    spec = Spec(
        tiers={"balanced": Tier(primary="gpt-4")},
        agents={
            "hub": Agent(tier="balanced", role=AgentRole.HUB, can_delegate=["worker"]),
            "worker": Agent(
                tier="balanced",
                role=AgentRole.WORKER,
                can_delegate=["hub"],
                delegate_via="cli",
            ),
        },
    )
    with pytest.raises(
        TopologyError, match="Delegation cycle detected: hub -> worker -> hub"
    ):
        validate_topology(spec)


def test_validate_topology_undefined_tier():
    spec = Spec(
        tiers={"balanced": Tier(primary="gpt-4")},
        agents={"hub": Agent(tier="unknown", role=AgentRole.HUB)},
    )
    with pytest.raises(TopologyError, match="references unknown tier 'unknown'"):
        validate_topology(spec)


def test_validate_topology_undefined_delegate():
    spec = Spec(
        tiers={"balanced": Tier(primary="gpt-4")},
        agents={
            "hub": Agent(tier="balanced", role=AgentRole.HUB, can_delegate=["ghost"])
        },
    )
    with pytest.raises(
        TopologyError, match="tries to delegate to undefined agent 'ghost'"
    ):
        validate_topology(spec)
