import yaml
from pathlib import Path
import typer
from rich.console import Console

console = Console()


def init_command(
    config: Path = typer.Option(
        Path("agents.yaml"), help="Path to create the spec file."
    ),
):
    """Scaffold a default agents.yaml configuration."""
    if config.exists():
        console.print(f"[yellow]Warning:[/yellow] {config} already exists. Aborting.")
        return

    default_spec = {
        "version": "1.0",
        "harness": {
            "opencode": {
                "capabilities": {"supports_subagent_model": True, "supports_mcp": True},
                "scopes": [
                    {"name": "default", "kind": "global", "path": "~/.opencode"}
                ],
            }
        },
        "tiers": {"balanced": {"primary": "gpt-4"}},
        "models": {"gpt-4": {"sources": [{"via": "openai", "id": "gpt-4"}]}},
        "agents": {"hub": {"tier": "balanced", "role": "hub"}},
    }

    config.write_text(yaml.dump(default_spec, sort_keys=False))
    console.print(f"[green]Initialized[/green] default spec at {config}")
