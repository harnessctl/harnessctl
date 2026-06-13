import asyncio
import typer
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich import box

from harnessctl.discovery.probes import discover_all
from harnessctl.discovery.status import get_all_services_status, ServiceStatus
from harnessctl.pricing.market import fetch_market_data
from harnessctl.pricing.catalog import merge_market_data, MarketModel
from harnessctl.discovery.base import run_probes
from harnessctl.discovery.ollama import OllamaProbe
from harnessctl.discovery.mlx import MLXProbe
from harnessctl.discovery.openai_compat import OpenAICompatProbe

console = Console()
models_app = typer.Typer(help="Manage and discover models.")


async def _get_local_models() -> List:
    probes = [
        OllamaProbe(),
        MLXProbe(),
        OpenAICompatProbe(runtime="lmstudio", endpoint="http://localhost:1234/v1"),
    ]
    return await run_probes(probes)


@models_app.command(name="list")
def list_cmd(
    ctx: typer.Context,
    local: bool = typer.Option(False, "--local", help="Filter only local models."),
    commercial: bool = typer.Option(
        False, "--commercial", help="Filter only commercial models."
    ),
    sort_by: str = typer.Option(
        "intelligence",
        "--sort-by",
        help="Sort by: intelligence, speed, price, context.",
    ),
    direction: str = typer.Option(
        "desc", "--direction", help="Sort direction: asc, desc."
    ),
    provider: Optional[str] = typer.Option(
        None, "--provider", help="Filter by provider (e.g. openai, anthropic, ollama)."
    ),
    grep: Optional[str] = typer.Option(None, "--grep", help="Filter by name."),
    refresh: bool = typer.Option(False, "--refresh", help="Force refresh market data."),
    reindex: bool = typer.Option(
        False, "--reindex", help="Clear cache and re-probe all services."
    ),
):
    """List existing models with intelligence, speed and price metrics."""

    async def _async_list():
        warnings = ctx.obj.warnings

        if reindex:
            from harnessctl.pricing.cache import clear_cache

            clear_cache()
            console.print("[yellow]Cache cleared. Re-probing services...[/yellow]")

        # 1. Probing and Discovery
        with console.status("[bold green]Probing services and fetching market data..."):
            services_task = get_all_services_status()
            market_task = fetch_market_data(warnings, force_refresh=refresh or reindex)

            # If not commercial-only, also discover local models
            local_models_task = (
                _get_local_models() if not commercial else asyncio.sleep(0, [])
            )

            services, market_models, local_discovered = await asyncio.gather(
                services_task, market_task, local_models_task
            )

        # 2. Merge and Filter
        catalog = merge_market_data(local_discovered, market_models)

        if local:
            catalog = [m for m in catalog if m.local]
        if commercial:
            catalog = [m for m in catalog if not m.local]
        if provider:
            catalog = [m for m in catalog if provider.lower() in m.provider.lower()]
        if grep:
            catalog = [
                m
                for m in catalog
                if grep.lower() in m.id.lower() or grep.lower() in m.name.lower()
            ]

        # 3. Sort
        reverse = direction.lower() == "desc"

        def sort_key(m: MarketModel):
            if sort_by == "intelligence":
                return m.intelligence
            if sort_by == "speed":
                return m.speed_tps
            if sort_by == "price":
                return m.input_per_mtok
            if sort_by == "context":
                return m.context_window
            return m.intelligence

        catalog.sort(key=sort_key, reverse=reverse)

        # 4. Render Service Status
        status_line = []
        for s in services:
            color = (
                "green"
                if s.status == ServiceStatus.ACTIVE
                else "yellow"
                if s.status == ServiceStatus.STARTED
                else "red"
            )
            status_line.append(f"[{color}]{s.name}: {s.status.value}[/{color}]")

        console.print(f"Services: {' | '.join(status_line)}")
        console.print()

        # 5. Render Table
        table = Table(title="Global Model Market & Local Discovery", box=box.ROUNDED)
        table.add_column("Model ID", style="cyan", no_wrap=True)
        table.add_column("Provider", style="magenta")
        table.add_column("Intel", justify="right")
        table.add_column("Speed (TPS)", justify="right")
        table.add_column("Price/1M (In/Out)", justify="right")
        table.add_column("Context", justify="right")

        for m in catalog:
            # Color coding
            intel_color = (
                "green"
                if m.intelligence >= 80
                else "yellow"
                if m.intelligence >= 50
                else "white"
            )
            price_color = "red" if m.input_per_mtok > 10 else "white"

            intel_str = f"[{intel_color}]{m.intelligence:.0f}[/{intel_color}]"
            speed_str = f"{m.speed_tps:.0f}" if m.speed_tps > 0 else "—"

            if m.local:
                price_str = "[green]FREE[/green]"
            else:
                price_str = f"[{price_color}]${m.input_per_mtok:.2f} / ${m.output_per_mtok:.2f}[/{price_color}]"

            ctx_str = (
                f"{m.context_window // 1000}k"
                if m.context_window >= 1000
                else str(m.context_window)
            )

            table.add_row(m.id, m.provider, intel_str, speed_str, price_str, ctx_str)

        console.print(table)

    asyncio.run(_async_list())


@models_app.command(name="discover")
def discover_cmd():
    """Discover local runtimes and models."""
    with console.status("Discovering local runtimes..."):
        models = discover_all()

    table = Table(title="Discovered Models")
    table.add_column("Runtime")
    table.add_column("Model ID")
    table.add_column("Endpoint")

    for m in models:
        table.add_row(m.runtime, m.id, m.endpoint)

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
    from harnessctl.recommend.ranker import search_candidates

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
