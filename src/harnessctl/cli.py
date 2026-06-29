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

config_app = typer.Typer(
    help="Manage routing configuration and bootstrap workflows.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

prompts_app = typer.Typer(
    help="Manage harness-aware prompt bundles.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

mcp_app = typer.Typer(
    help="MCP entrypoints for integration with external orchestrators.",
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


def _not_implemented(command_name: str) -> None:
    typer.secho(f"Not implemented yet: {command_name}", fg=typer.colors.YELLOW)
    raise typer.Exit(code=2)


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
app.add_typer(config_app, name="config")
app.add_typer(prompts_app, name="prompts")
app.add_typer(mcp_app, name="mcp")


@config_app.command(name="init")
def config_init_stub(
    provider: str = typer.Option(
        ..., "--provider", help="Provider preset to bootstrap."
    ),
    global_scope: bool = typer.Option(
        False,
        "--global",
        help="Initialize config under ~/.config/harnessctl.",
    ),
    project: Optional[Path] = typer.Option(
        None,
        "--project",
        help="Initialize config under <path>/.harnessctl.",
    ),
) -> None:
    """Bootstrap routing configuration (stub)."""
    _ = (provider, global_scope, project)
    _not_implemented("config init")


@prompts_app.command(name="install")
def prompts_install_stub(
    harness: list[str] = typer.Option(
        ...,
        "--harness",
        help="Target harness identifier. Repeat to install multiple.",
    ),
    version: str = typer.Option("v1", "--version", help="Prompt bundle version."),
    global_scope: bool = typer.Option(
        False,
        "--global",
        help="Install under ~/.config/harnessctl/prompts.",
    ),
    project: Optional[Path] = typer.Option(
        None,
        "--project",
        help="Install under <path>/.harnessctl/prompts.",
    ),
    overwrite: bool = typer.Option(
        False, "--overwrite", help="Overwrite existing files."
    ),
) -> None:
    """Install prompt bundles into harnessctl-managed paths (stub)."""
    _ = (harness, version, global_scope, project, overwrite)
    _not_implemented("prompts install")


@prompts_app.command(name="render")
def prompts_render_stub(
    harness: list[str] = typer.Option(
        ...,
        "--harness",
        help="Target harness identifier. Repeat to render multiple.",
    ),
    version: str = typer.Option("v1", "--version", help="Prompt bundle version."),
    cli_output: bool = typer.Option(
        False,
        "--cli",
        help="Render bundle content to stdout.",
    ),
) -> None:
    """Render prompt bundles for manual copy/use (stub)."""
    _ = (harness, version, cli_output)
    _not_implemented("prompts render")


@mcp_app.command(name="select_model_for_task")
def mcp_select_model_for_task_stub() -> None:
    """MCP model selection entrypoint (stub)."""
    _not_implemented("mcp select_model_for_task")


@app.command()
def version():
    """Show the version of harnessctl."""
    typer.echo("harnessctl 0.1.0")


def run():
    app()


if __name__ == "__main__":
    run()
