"""Tests for harnessctl.emit.registry auto-registration."""

from harnessctl.emit.opencode import OpenCodeEmitter
from harnessctl.emit.pi import PiEmitter
from harnessctl.emit.registry import emitter_registry


class TestAutoRegistration:
    def test_opencode_registered(self) -> None:
        cls = emitter_registry.get("opencode")
        assert cls is OpenCodeEmitter

    def test_pi_registered(self) -> None:
        cls = emitter_registry.get("pi")
        assert cls is PiEmitter

    def test_list_ids_contains_both(self) -> None:
        ids = emitter_registry.list_ids()
        assert "opencode" in ids
        assert "pi" in ids
