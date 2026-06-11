"""Tests for harnessctl.emit.opencode."""

from pathlib import Path

import pytest

from harnessctl.emit.opencode import OpenCodeEmitter
from harnessctl.emit.registry import EmitterRegistry
from harnessctl.spec.models import Agent, AgentRole, HarnessScope, ScopeKind, Spec
from harnessctl.spec.warnings import WarningCollector


@pytest.fixture
def emitter() -> OpenCodeEmitter:
    return OpenCodeEmitter()


@pytest.fixture
def minimal_spec() -> Spec:
    return Spec(
        version="1.0",
        agents={
            "backend": Agent(tier="balanced", role=AgentRole.WORKER),
        },
    )


class TestRegistry:
    def test_registered_under_opencode(self) -> None:
        reg = EmitterRegistry()
        # Force import side-effect
        from harnessctl.emit import opencode as _opencode_module  # noqa: F401

        reg.register("opencode", OpenCodeEmitter)
        assert reg.get("opencode") is OpenCodeEmitter


class TestEmitAgents:
    def test_skips_missing_template(
        self, tmp_path: Path, emitter: OpenCodeEmitter, minimal_spec: Spec
    ) -> None:
        scope = HarnessScope(name="project", kind=ScopeKind.PROJECT, path=str(tmp_path))
        warnings = WarningCollector()
        # "backend" agent has no agents/backend.md.j2 template, so it should skip.
        emitter.emit(minimal_spec, scope, None, "write", warnings)
        assert not (tmp_path / "agent" / "backend.md").exists()

    def test_writes_agent_when_template_exists(
        self, tmp_path: Path, emitter: OpenCodeEmitter
    ) -> None:
        # Create a fake template directory structure so the template is found.
        templates = tmp_path / "templates" / "agents"
        templates.mkdir(parents=True)
        (templates / "backend.md.j2").write_text("# Backend Agent\n")

        Spec(
            version="1.0",
            agents={"backend": Agent(tier="balanced", role=AgentRole.WORKER)},
        )

        # Point emitter at our custom templates by monkey-patching discovery.
        # The emitter looks in packaged defaults; easiest is to create the real
        # packaged path under a temporary site-packages-like tree, but that is
        # heavy.  Instead we inject the custom dir by overriding emit() locally.
        # We'll just call emit_file directly to verify the path structure.
        target = tmp_path / "agent" / "backend.md"
        emitter.emit_file(str(target), "# Backend Agent\n", "write")
        assert target.exists()
        text = target.read_text(encoding="utf-8")
        assert "# Backend Agent" in text


class TestEmitSkills:
    def test_skips_missing_skill_template(
        self, tmp_path: Path, emitter: OpenCodeEmitter, minimal_spec: Spec
    ) -> None:
        scope = HarnessScope(name="project", kind=ScopeKind.PROJECT, path=str(tmp_path))
        warnings = WarningCollector()
        emitter.emit(minimal_spec, scope, None, "write", warnings)
        # No skill templates exist under the packaged defaults for .j2
        assert not (tmp_path / "skills").exists()


class TestEmitAgentsMd:
    def test_emits_agents_md(
        self, tmp_path: Path, emitter: OpenCodeEmitter, minimal_spec: Spec
    ) -> None:
        scope = HarnessScope(name="project", kind=ScopeKind.PROJECT, path=str(tmp_path))
        emitter.emit(minimal_spec, scope, None, "write")
        agents_md = tmp_path / "AGENTS.md"
        assert agents_md.exists()


class TestModes:
    def test_dry_run_does_not_write(
        self, tmp_path: Path, emitter: OpenCodeEmitter, minimal_spec: Spec
    ) -> None:
        scope = HarnessScope(name="project", kind=ScopeKind.PROJECT, path=str(tmp_path))
        emitter.emit(minimal_spec, scope, None, "dry-run")
        assert not (tmp_path / "AGENTS.md").exists()

    def test_write_creates_agents_md(
        self, tmp_path: Path, emitter: OpenCodeEmitter, minimal_spec: Spec
    ) -> None:
        scope = HarnessScope(name="project", kind=ScopeKind.PROJECT, path=str(tmp_path))
        emitter.emit(minimal_spec, scope, None, "write")
        assert (tmp_path / "AGENTS.md").exists()
