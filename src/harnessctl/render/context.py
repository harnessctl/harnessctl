"""Rendering context builder for harnessctl templates."""

from harnessctl.spec.models import HarnessCapabilities, HarnessTarget, Spec


class HarnessContext:
    """Exposes a harness target's capabilities and metadata to templates.

    Attributes are accessed directly in Jinja (e.g. ``harness.supports_mcp``).
    """

    def __init__(self, target: HarnessTarget, harness_id: str) -> None:
        self._target = target
        self._id = harness_id

    @property
    def id(self) -> str:  # noqa: A003
        """Harness identifier."""
        return self._id

    @property
    def supports_mcp(self) -> bool:
        return self._target.capabilities.supports_mcp

    @property
    def supports_subagent_model(self) -> bool:
        return self._target.capabilities.supports_subagent_model

    @property
    def supports_tool_permissions(self) -> str:
        return self._target.capabilities.supports_tool_permissions

    def __repr__(self) -> str:
        return f"HarnessContext(id={self._id!r})"


def build_context(spec: Spec, harness_id: str) -> dict:
    """Build the dict injected into Jinja2 templates.

    Args:
        spec: The full validated ``Spec`` object.
        harness_id: Key into ``spec.harness`` for the current target.

    Returns:
        A dict with ``spec`` and ``harness`` keys ready for rendering.

    Raises:
        KeyError: If *harness_id* is not present in ``spec.harness``.
    """
    target = spec.harness.get(harness_id)
    if target is None:
        # Gracefully degrade when the harness target is absent from the spec.
        target = HarnessTarget(capabilities=HarnessCapabilities())
    return {
        "spec": spec,
        "harness": HarnessContext(target, harness_id),
    }
