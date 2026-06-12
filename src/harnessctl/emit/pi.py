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
        self.emit_settings(spec, base_path, mode, warnings)

    def emit_settings(
        self,
        spec: Spec,
        base_path: str,
        mode: str,
        warnings: WarningCollector,
    ) -> None:
        """Emit mcp and model settings into settings.json."""
        from harnessctl.providers.resolver import ProviderResolver
        from harnessctl.emit.jsonmerge import merge_json_content

        managed_data = {}
        target = spec.harness.get(self.HARNESS_ID)

        # MCP
        if target and target.capabilities.supports_mcp:
            servers = {}
            for name, mcp in spec.mcp.items():
                if mcp.disabled:
                    continue
                if not mcp.command:
                    warnings.add(
                        field="mcp",
                        reason=f"MCP server '{name}' has no command, pi only supports stdio.",
                        harness=self.HARNESS_ID,
                    )
                    continue
                servers[name] = {
                    "command": mcp.command,
                    "args": mcp.args,
                    "env": mcp.env,
                }
            if servers:
                managed_data["mcpServers"] = servers
        elif spec.mcp:
            warnings.add(
                field="mcp",
                reason=f"Harness '{self.HARNESS_ID}' does not support MCP.",
                harness=self.HARNESS_ID,
            )

        # Models
        models = {}
        for name, model in spec.models.items():
            if not model.sources:
                continue
            conn = ProviderResolver.resolve(model.sources[0])
            m_dict = {"provider": conn.kind, "modelId": conn.model_id}
            if conn.base_url:
                m_dict["baseUrl"] = conn.base_url
            if conn.key_ref:
                m_dict["apiKey"] = conn.key_ref
            models[name] = m_dict

        if models:
            managed_data["models"] = models

        if not managed_data:
            return

        settings_path = Path(base_path) / "settings.json"
        existing_content = ""
        if settings_path.exists():
            existing_content = settings_path.read_text(encoding="utf-8")

        new_content = merge_json_content(existing_content, managed_data)
        self._write_content_with_mode(
            settings_path, new_content, existing_content, mode
        )
