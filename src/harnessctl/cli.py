import sys
from pathlib import Path
from typing import Optional

import typer
import yaml
from rich.console import Console

from harnessctl.config.schema_validator import (
    RoutingConfigSchemaError,
    validate_routing_config_document,
)
from harnessctl.config.preset_loader import (
    build_routing_config_from_preset,
)
from harnessctl.paths import (
    ensure_directory,
    get_global_config_base_dir,
    get_project_config_base_dir,
)
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
def config_init_command(
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
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite existing generated config files.",
    ),
) -> None:
    """Bootstrap routing configuration for a selected provider."""
    if global_scope == (project is not None):
        typer.secho(
            "You must specify exactly one target: --global or --project <path>",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=2)

    try:
        routing_doc = build_routing_config_from_preset(provider)
    except ValueError as exc:
        typer.secho(str(exc), fg=typer.colors.RED)
        raise typer.Exit(code=2) from exc

    try:
        validate_routing_config_document(routing_doc)
    except RoutingConfigSchemaError as exc:
        typer.secho(f"Generated config failed validation: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=2) from exc

    if global_scope:
        base_dir = get_global_config_base_dir()
    else:
        base_dir = get_project_config_base_dir(project)

    config_path = base_dir / "config.yaml"

    existing = [str(path) for path in (config_path,) if path.exists()]
    if existing and not overwrite:
        typer.secho(
            "Refusing to overwrite existing files (use --overwrite):\n"
            + "\n".join(f"- {path}" for path in existing),
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=2)

    ensure_directory(base_dir)

    config_path.write_text(
        yaml.safe_dump(routing_doc, sort_keys=False), encoding="utf-8"
    )

    typer.secho(
        f"Initialized config:\n- {config_path}",
        fg=typer.colors.GREEN,
    )


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
