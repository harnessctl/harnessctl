import typer
from rich.console import Console
from rich.table import Table

from harnessctl.discovery.probes import discover_all
from harnessctl.recommend.ranker import search_candidates

console = Console()

models_app = typer.Typer(help="Manage and discover models.")


@models_app.command(name="discover")
def discover_cmd():
    """Discover local runtimes and models (Ollama, MLX)."""
    with console.status("Discovering local runtimes..."):
        models = discover_all()

    table = Table(title="Discovered Models")
    table.add_column("Runtime")
    table.add_column("Model ID")
    table.add_column("Endpoint")

    for m in models:
        table.add_row(m.runtime, m.id, m.endpoint)

    console.print(table)


@models_app.command(name="list")
def list_cmd(ctx: typer.Context):
    """List models defined in the spec."""
    spec = ctx.obj.spec
    table = Table(title="Spec Models")
    table.add_column("Model ID")
    table.add_column("Sources")

    for name, model in spec.models.items():
        sources = ", ".join([f"{s.via.value}:{s.id}" for s in model.sources])
        table.add_row(name, sources)

    console.print(table)


@models_app.command(name="recommend")
def recommend_cmd(
    ctx: typer.Context,
    task: str = typer.Argument(
        ..., help="The task description to recommend a model for."
    ),
):
    """Recommend a model for a specific task based on system hardware."""
    from harnessctl.sysprobe.profile import get_system_profile

    profile = get_system_profile()

    console.print(f"Recommending for task: [bold]{task}[/bold]")
    console.print(
        f"System: {profile.total_ram_gb:.1f}GB RAM, {profile.total_vram_gb:.1f}GB VRAM"
    )

    with console.status("Searching for candidates..."):
        candidates = search_candidates(profile, tags=["gguf", "coding", "instruct"])

    if not candidates:
        console.print("[yellow]No suitable local models found on HuggingFace.[/yellow]")
        return

    table = Table(title="Top Recommendations")
    table.add_column("Score", justify="right")
    table.add_column("Model")
    table.add_column("Quant")
    table.add_column("Memory (Est)")

    for c in candidates[:5]:
        table.add_row(
            f"{c.score:.1f}", c.repo_id, c.quant, f"{c.estimated_memory_gb:.1f} GB"
        )

    console.print(table)
