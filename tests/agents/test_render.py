from harnessctl.spec.models import (
    Spec,
    Agent,
    AgentRole,
    Tier,
    HarnessTarget,
    HarnessCapabilities,
    HarnessScope,
)
from harnessctl.emit.opencode import OpenCodeEmitter


def test_render_agents_with_role_and_tier_fallbacks(tmp_path):
    # Setup spec
    spec = Spec(
        tiers={
            "reasoning": Tier(primary="gpt-4-reasoning"),
            "balanced": Tier(primary="gpt-4"),
            "cheap_local": Tier(primary="llama3"),
        },
        agents={
            "my_hub": Agent(tier="balanced", role=AgentRole.HUB),
            "thinker_agent": Agent(tier="reasoning", role=AgentRole.WORKER),
            "custom_agent": Agent(tier="cheap_local", role=AgentRole.WORKER),
        },
        harness={
            "opencode": HarnessTarget(
                capabilities=HarnessCapabilities(supports_subagent_model=True),
                scopes=[
                    HarnessScope(name="default", kind="global", path=str(tmp_path))
                ],
            )
        },
    )

    emitter = OpenCodeEmitter()
    emitter.emit(spec, spec.harness["opencode"].scopes[0], None, mode="write")

    # Check rendered files
    agent_dir = tmp_path / "agent"
    assert (agent_dir / "my_hub.md").exists()
    assert (agent_dir / "thinker_agent.md").exists()
    assert (agent_dir / "custom_agent.md").exists()

    # Verify content of my_hub.md (should use hub.md.j2)
    hub_content = (agent_dir / "my_hub.md").read_text()
    assert "ROLE: Orchestrator (Hub)" in hub_content
    assert "VERDICT PROTOCOL" in hub_content

    # Verify content of thinker_agent.md (should use reasoning.md.j2 via tier fallback)
    thinker_content = (agent_dir / "thinker_agent.md").read_text()
    assert "ROLE: Thinker (Reasoning Tier)" in thinker_content
    assert "VERDICT PROTOCOL" in thinker_content


def test_render_model_injection_fallback(tmp_path):
    # Setup spec with a harness that does NOT support subagent models
    spec = Spec(
        tiers={"balanced": Tier(primary="gpt-4")},
        agents={"my_agent": Agent(tier="balanced", role=AgentRole.WORKER)},
        harness={
            "opencode": HarnessTarget(
                capabilities=HarnessCapabilities(supports_subagent_model=False),
                scopes=[
                    HarnessScope(name="default", kind="global", path=str(tmp_path))
                ],
            )
        },
    )

    emitter = OpenCodeEmitter()
    emitter.emit(spec, spec.harness["opencode"].scopes[0], None, mode="write")

    content = (tmp_path / "agent" / "my_agent.md").read_text()
    assert "MODEL: gpt-4" in content
    assert "ROLE: Mid-Tier Agent (Balanced)" in content
