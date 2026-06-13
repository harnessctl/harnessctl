import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from harnessctl.spec.loader import load_spec
from harnessctl.spec.models import Spec
from harnessctl.spec.warnings import WarningCollector
from harnessctl.commands.init import init_command
from harnessctl.commands.validate import validate_command
from harnessctl.commands.compile import compile_command
from harnessctl.commands.models import models_app, discover_cmd
from harnessctl.commands.agents import agents_app
from harnessctl.commands.recommend import recommend_cmd
from harnessctl.commands.auth import auth_app

app = typer.Typer(
    help="harnessctl: Manage AI harness configurations and agents.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

err_console = Console(stderr=True)
console = Console()


class AppContext:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.warnings = WarningCollector()
        self._spec: Optional[Spec] = None

    @property
    def spec(self) -> Spec:
        if self._spec is None:
            try:
                self._spec = load_spec(self.config_path, self.warnings)
            except Exception as e:
                # Use plain print if typer.echo is also being eaten/transformed
                print(f"Error loading spec: {e}", file=sys.stderr)
                raise typer.Exit(code=2)
        return self._spec


@app.callback()
def main(
    ctx: typer.Context,
    config: Path = typer.Option(
        Path("agents.yaml"),
        "--config",
        "-c",
        help="Path to the agents.yaml spec file.",
        envvar="HARNESSCTL_CONFIG",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output."
    ),
):
    """
    Global configuration for harnessctl.
    """
    ctx.obj = AppContext(config)


app.command(name="init")(init_command)
app.command(name="validate")(validate_command)
app.command(name="compile")(compile_command)
app.command(name="discover")(discover_cmd)
app.command(name="recommend")(recommend_cmd)
app.add_typer(models_app, name="models")
app.add_typer(agents_app, name="agents")
app.add_typer(auth_app, name="auth")


@app.command()
def version():
    """Show the version of harnessctl."""
    typer.echo("harnessctl 0.1.0")


def run():
    app()


if __name__ == "__main__":
    run()
