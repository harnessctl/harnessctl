"""Pi.dev harness emitter for harnessctl."""

from __future__ import annotations

from pathlib import Path

from harnessctl.emit.base import Emitter
from harnessctl.emit.paths import resolve_path

from harnessctl.spec.models import HarnessScope, Spec
from harnessctl.spec.warnings import WarningCollector


class PiEmitter(Emitter):
    """Emitter for the Pi.dev harness.

    Very similar to :class:`OpenCodeEmitter`, but writes into Pi-specific
    directory layouts and warns when a custom scope requires a ``launch_env``
    variable.
    """

    HARNESS_ID = "pi"

    def emit(
        self,
        spec: Spec,
        scope: HarnessScope,
        project_dir: str | None,
        mode: str,
        warnings: WarningCollector | None = None,
    ) -> None:
        """Emit spec artifacts for the Pi harness into *scope*.

        Args:
            spec: The canonical spec.
            scope: Destination scope (path, kind, etc.).
            project_dir: Optional project directory for ``{project}`` resolution.
            mode: ``dry-run``, ``diff``, ``check``, or ``write``.
            warnings: Collector for non-fatal issues.
        """
        if warnings is None:
            warnings = WarningCollector()

        if scope.launch_env:
            for var in scope.launch_env:
                warnings.add(
                    field="scope",
                    reason=f"To use custom scope {scope.name}, you must set {var}",
                    harness=self.HARNESS_ID,
                )

        base_path = resolve_path(scope.path, project_dir)
        self._emit_templates(
            spec, base_path, mode, agent_dir="agent", skills_dir="skills"
        )

    def emit_file(self, target_path: str, content: str, mode: str) -> None:
        """Emit *content* to *target_path* using the given *mode*."""
        from harnessctl.emit.base import FileChangedError

        path = Path(target_path)
        full_content = self._prepend_marker(content)

        if mode == "dry-run":
            return

        if mode == "diff":
            if path.exists():
                existing = path.read_text(encoding="utf-8")
                if existing == full_content:
                    return
                diff = self._unified_diff(existing, full_content, target_path)
                raise FileChangedError(target_path, diff)
            return

        if mode == "check":
            if path.exists():
                existing = path.read_text(encoding="utf-8")
                if existing != full_content:
                    diff = self._unified_diff(existing, full_content, target_path)
                    raise FileChangedError(target_path, diff)
            else:
                raise FileChangedError(
                    target_path, f"File {target_path!r} does not exist."
                )
            return

        if mode == "write":
            self._backup_if_needed(path)
            path.parent.mkdir(parents=True, exist_ok=True)
            self._atomic_write(path, full_content)
            return

        raise ValueError(f"Unknown mode: {mode!r}")
