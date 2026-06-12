"""Tests for harnessctl.emit.pi."""

from pathlib import Path

import pytest

from harnessctl.emit.pi import PiEmitter
from harnessctl.emit.registry import EmitterRegistry
from harnessctl.spec.models import Agent, AgentRole, HarnessScope, ScopeKind, Spec
from harnessctl.spec.warnings import WarningCollector


@pytest.fixture
def emitter() -> PiEmitter:
    return PiEmitter()


@pytest.fixture
def minimal_spec() -> Spec:
    return Spec(
        version="1.0",
        agents={
            "backend": Agent(tier="unknown_tier", role=AgentRole.WORKER),
        },
    )


class TestRegistry:
    def test_registered_under_pi(self) -> None:
        reg = EmitterRegistry()
        from harnessctl.emit import pi as _pi_module  # noqa: F401

        reg.register("pi", PiEmitter)
        assert reg.get("pi") is PiEmitter


class TestLaunchEnvWarning:
    def test_warns_when_launch_env_present(
        self, tmp_path: Path, emitter: PiEmitter, minimal_spec: Spec
    ) -> None:
        scope = HarnessScope(
            name="custom",
            kind=ScopeKind.CUSTOM,
            path=str(tmp_path),
            launch_env={"PI_CODING_AGENT_DIR": str(tmp_path)},
        )
        warnings = WarningCollector()
        emitter.emit(minimal_spec, scope, None, "dry-run", warnings)
        assert any(
            w.field == "scope" and "PI_CODING_AGENT_DIR" in w.reason
            for w in warnings.warnings
        )

    def test_no_warning_without_launch_env(
        self, tmp_path: Path, emitter: PiEmitter, minimal_spec: Spec
    ) -> None:
        scope = HarnessScope(name="project", kind=ScopeKind.PROJECT, path=str(tmp_path))
        warnings = WarningCollector()
        emitter.emit(minimal_spec, scope, None, "dry-run", warnings)
        assert not warnings.has_warnings()


class TestEmitAgents:
    def test_skips_missing_template(
        self, tmp_path: Path, emitter: PiEmitter, minimal_spec: Spec
    ) -> None:
        scope = HarnessScope(name="project", kind=ScopeKind.PROJECT, path=str(tmp_path))
        warnings = WarningCollector()
        emitter.emit(minimal_spec, scope, None, "write", warnings)
        assert not (tmp_path / "agent" / "backend.md").exists()

    def test_writes_agent_when_template_exists(
        self, tmp_path: Path, emitter: PiEmitter
    ) -> None:
        target = tmp_path / "agent" / "backend.md"
        emitter.emit_file(str(target), "# Backend Agent\n", "write")
        assert target.exists()
        text = target.read_text(encoding="utf-8")
        assert "# Backend Agent" in text


class TestEmitSkills:
    def test_emits_skill_when_template_exists(
        self, tmp_path: Path, emitter: PiEmitter, minimal_spec: Spec
    ) -> None:
        scope = HarnessScope(name="project", kind=ScopeKind.PROJECT, path=str(tmp_path))
        emitter.emit(minimal_spec, scope, None, "write")
        assert (tmp_path / "skills" / "clean-code" / "SKILL.md").exists()


class TestModes:
    def test_dry_run_does_not_write(
        self, tmp_path: Path, emitter: PiEmitter, minimal_spec: Spec
    ) -> None:
        scope = HarnessScope(name="project", kind=ScopeKind.PROJECT, path=str(tmp_path))
        emitter.emit(minimal_spec, scope, None, "dry-run")
        # No files should be created
        assert not (tmp_path / "agent").exists()
        assert not (tmp_path / "skills").exists()

    def test_write_creates_agent_dir(self, tmp_path: Path, emitter: PiEmitter) -> None:
        # When a template exists, write should create the directory.
        target = tmp_path / "agent" / "backend.md"
        emitter.emit_file(str(target), "content", "write")
        assert target.exists()
