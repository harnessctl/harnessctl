"""Emitter registry for harnessctl."""

from __future__ import annotations

from harnessctl.emit.base import Emitter


class EmitterRegistry:
    """Simple registry mapping harness IDs to concrete :class:`Emitter` classes."""

    def __init__(self) -> None:
        self._registry: dict[str, type[Emitter]] = {}

    def register(self, harness_id: str, emitter_cls: type[Emitter]) -> None:
        """Register *emitter_cls* for the given *harness_id*."""
        self._registry[harness_id] = emitter_cls

    def get(self, harness_id: str) -> type[Emitter]:
        """Return the emitter class registered for *harness_id*.

        Raises:
            KeyError: If no emitter is registered for *harness_id*.
        """
        try:
            return self._registry[harness_id]
        except KeyError as exc:
            raise KeyError(f"No emitter registered for harness {harness_id!r}") from exc

    def list_ids(self) -> list[str]:
        """Return a sorted list of registered harness IDs."""
        return sorted(self._registry.keys())


# Global singleton registry used by the CLI / compiler.
_REGISTRY: EmitterRegistry | None = None


def get_registry() -> EmitterRegistry:
    """Return the global :class:`EmitterRegistry`, creating it if necessary."""
    global _REGISTRY  # noqa: PLW0603
    if _REGISTRY is None:
        _REGISTRY = EmitterRegistry()
    return _REGISTRY


# Auto-register concrete emitters when the registry module is imported.
from harnessctl.emit.opencode import OpenCodeEmitter  # noqa: E402
from harnessctl.emit.pi import PiEmitter  # noqa: E402

get_registry().register(OpenCodeEmitter.HARNESS_ID, OpenCodeEmitter)
get_registry().register(PiEmitter.HARNESS_ID, PiEmitter)

# Module-level convenience alias for consumers.
emitter_registry = get_registry()
