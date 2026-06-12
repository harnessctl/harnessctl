import sys
import typer
from rich.console import Console
from rich.table import Table

console = Console()
err_console = Console(stderr=True)


def validate_command(ctx: typer.Context):
    """Load and validate the spec file, printing any warnings."""
    app_ctx = ctx.obj
    # Accessing spec property triggers load and validation
    try:
        _ = app_ctx.spec
    except Exception:
        # Error already printed by AppContext
        sys.exit(2)

    if app_ctx.warnings.has_warnings():
        table = Table(
            title="Spec Warnings", show_header=True, header_style="bold yellow"
        )
        table.add_column("Harness")
        table.add_column("Field")
        table.add_column("Reason")

        for w in app_ctx.warnings.warnings:
            table.add_row(w.harness or "-", w.field or "-", w.reason)

        console.print(table)
    else:
        console.print("[green]Spec is valid.[/green]")
