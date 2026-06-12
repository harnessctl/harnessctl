"""OpenCode harness emitter for harnessctl."""

from __future__ import annotations

from pathlib import Path

from harnessctl.emit.base import Emitter
from harnessctl.emit.paths import resolve_path

from harnessctl.spec.models import HarnessScope, Spec
from harnessctl.spec.warnings import WarningCollector


class OpenCodeEmitter(Emitter):
    """Emitter for the OpenCode harness.

    Renders agent and skill templates into the target directory tree.
    """

    HARNESS_ID = "opencode"

    def emit(
        self,
        spec: Spec,
        scope: HarnessScope,
        project_dir: str | None,
        mode: str,
        warnings: WarningCollector | None = None,
    ) -> None:
        """Emit spec artifacts for the OpenCode harness into *scope*.

        Args:
            spec: The canonical spec.
            scope: Destination scope (path, kind, etc.).
            project_dir: Optional project directory for ``{project}`` resolution.
            mode: ``dry-run``, ``diff``, ``check``, or ``write``.
            warnings: Collector for non-fatal issues.
        """
        if warnings is None:
            warnings = WarningCollector()

        base_path = resolve_path(scope.path, project_dir)
        self._emit_templates(
            spec, base_path, mode, agent_dir="agent", skills_dir="skills"
        )

        # --- unified AGENTS.md ---
        # For now emit an empty placeholder; a future template can replace this.
        agents_md_target = Path(base_path) / "AGENTS.md"
        self.emit_file(str(agents_md_target), "", mode)

        # --- settings (opencode.json) ---
        self.emit_settings(spec, base_path, mode, warnings)

    def emit_settings(
        self,
        spec: Spec,
        base_path: str,
        mode: str,
        warnings: WarningCollector,
    ) -> None:
        """Emit mcp and provider/model settings into opencode.json."""
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
                # opencode uses stdio mostly, we assume stdio if command is set
                if not mcp.command:
                    warnings.add_warning(
                        f"MCP server '{name}' has no command, opencode only supports stdio. Skipping."
                    )
                    continue
                servers[name] = {
                    "command": mcp.command,
                    "args": mcp.args,
                    "env": mcp.env,
                }
            if servers:
                managed_data["mcp"] = {"servers": servers}
        elif spec.mcp:
            warnings.add_warning(
                f"Harness '{self.HARNESS_ID}' does not support MCP. Skipping MCP servers."
            )

        # Models
        providers = {}
        models = {}
        for name, model in spec.models.items():
            if not model.sources:
                continue
            conn = ProviderResolver.resolve(model.sources[0])
            provider_name = f"provider_{conn.kind}"

            # Use dictionary keys dynamically
            providers[provider_name] = {"type": conn.kind}
            if conn.base_url:
                providers[provider_name]["url"] = conn.base_url
            if conn.key_ref:
                providers[provider_name]["apiKey"] = conn.key_ref

            models[name] = {"provider": provider_name, "id": conn.model_id}

        if providers:
            managed_data["provider"] = providers
        if models:
            managed_data["model"] = models

        if not managed_data:
            return

        settings_path = Path(base_path) / "opencode.json"
        existing_content = ""
        if settings_path.exists():
            existing_content = settings_path.read_text(encoding="utf-8")

        new_content = merge_json_content(existing_content, managed_data)
        self._write_content_with_mode(
            settings_path, new_content, existing_content, mode
        )
