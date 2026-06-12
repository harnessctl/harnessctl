import sys
from pathlib import Path
from typing import List, Optional
import typer
from rich.console import Console

from harnessctl.emit.registry import EmitterRegistry

console = Console()
err_console = Console(stderr=True)


def compile_command(
    ctx: typer.Context,
    harness_id: Optional[str] = typer.Option(
        None, "--harness", help="Filter by harness ID."
    ),
    scopes: Optional[List[str]] = typer.Option(
        None, "--scope", help="Filter by scope names."
    ),
    project_dir: Optional[Path] = typer.Option(
        None, "--project", help="Override project directory."
    ),
    mode: str = typer.Option(
        "write", "--mode", help="Mode: dry-run, diff, check, write."
    ),
):
    """Render and emit configurations to target harnesses."""
    app_ctx = ctx.obj
    spec = app_ctx.spec

    registry = EmitterRegistry()
    # Force registration
    from harnessctl.emit import opencode, pi  # noqa: F401

    targets = spec.harness.keys()
    if harness_id:
        if harness_id not in targets:
            err_console.print(
                f"[red]Error:[/red] Harness '{harness_id}' not found in spec."
            )
            sys.exit(1)
        targets = [harness_id]

    for hid in targets:
        emitter_cls = registry.get(hid)
        if not emitter_cls:
            err_console.print(
                f"[yellow]Warning:[/yellow] No emitter found for harness '{hid}'. Skipping."
            )
            continue

        emitter = emitter_cls()
        harness_target = spec.harness[hid]

        target_scopes = harness_target.scopes
        if scopes:
            target_scopes = [s for s in target_scopes if s.name in scopes]

        for scope in target_scopes:
            if not scope.enabled:
                continue

            console.print(
                f"Compiling for [bold]{hid}[/bold] (scope: {scope.name}) mode={mode}..."
            )
            try:
                emitter.emit(
                    spec=spec,
                    scope=scope,
                    project_dir=str(project_dir) if project_dir else None,
                    mode=mode,
                    warnings=app_ctx.warnings,
                )
            except Exception as e:
                err_console.print(
                    f"[red]Error emitting for {hid}/{scope.name}:[/red] {e}"
                )
                if mode == "check":
                    sys.exit(3)
                sys.exit(1)

    if app_ctx.warnings.has_warnings():
        console.print(
            f"\n[yellow]Completed with {len(app_ctx.warnings.warnings)} warnings.[/yellow]"
        )
    else:
        console.print("\n[green]Compilation successful.[/green]")
