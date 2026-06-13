import asyncio
import typer
from rich.console import Console
from rich.table import Table
from rich import box

from harnessctl.discovery.status import get_all_services_status
from harnessctl.pricing.market import fetch_market_data
from harnessctl.pricing.catalog import merge_market_data
from harnessctl.sysprobe.profile import detect_system
from harnessctl.recommend.engine import RecommendationEngine, PROFILES
from harnessctl.commands.models import _get_local_models

console = Console()


def recommend_cmd(
    ctx: typer.Context,
    profile: str = typer.Argument(
        "chat", help=f"Task profile: {', '.join(PROFILES.keys())}"
    ),
    limit: int = typer.Option(5, "--limit", "-n", help="Number of recommendations."),
    min_intel: float = typer.Option(0, "--min-intel", help="Min intelligence (0-100)."),
    max_intel: float = typer.Option(
        100, "--max-intel", help="Max intelligence (0-100)."
    ),
    min_speed: float = typer.Option(0, "--min-speed", help="Min speed (TPS)."),
    max_speed: float = typer.Option(
        float("inf"), "--max-speed", help="Max speed (TPS)."
    ),
    min_price: float = typer.Option(
        0, "--min-price", help="Min price per MTok (output)."
    ),
    max_price: float = typer.Option(
        float("inf"), "--max-price", help="Max price per MTok (output)."
    ),
    local_only: bool = typer.Option(
        False, "--local", help="Recommend only local models."
    ),
    commercial_only: bool = typer.Option(
        False, "--commercial", help="Recommend only commercial models."
    ),
    refresh: bool = typer.Option(False, "--refresh", help="Force refresh market data."),
):
    """Recommend the best models for a task based on hardware and market data."""

    async def _async_recommend():
        warnings = ctx.obj.warnings

        with console.status("[bold green]Analyzing system and market data..."):
            # 1. System Profile
            sys_profile = detect_system()

            # 2. Aggregation
            services_task = get_all_services_status()
            market_task = fetch_market_data(warnings, force_refresh=refresh)
            local_models_task = (
                _get_local_models() if not commercial_only else asyncio.sleep(0, [])
            )

            _, market_models, local_discovered = await asyncio.gather(
                services_task, market_task, local_models_task
            )

            catalog = merge_market_data(local_discovered, market_models)

        # 3. Engine
        engine = RecommendationEngine(sys_profile)
        recommendations = engine.recommend(
            catalog,
            profile_name=profile,
            limit=limit,
            min_intel=min_intel,
            max_intel=max_intel,
            min_speed=min_speed,
            max_speed=max_speed,
            min_price=min_price,
            max_price=max_price,
            local_only=local_only,
            commercial_only=commercial_only,
        )

        if not recommendations:
            console.print(
                "[yellow]No suitable models found matching your criteria.[/yellow]"
            )
            return

        # 4. Render Table
        table = Table(
            title=f"Recommendations: [bold cyan]{profile}[/bold cyan] Profile",
            box=box.ROUNDED,
        )
        table.add_column("Rank", justify="center")
        table.add_column("Score", justify="right", style="bold green")
        table.add_column("Model ID", style="cyan")
        table.add_column("Provider", style="magenta")
        table.add_column("Intel", justify="right")
        table.add_column("Speed", justify="right")
        table.add_column("Price/1M", justify="right")

        for i, rec in enumerate(recommendations, 1):
            m = rec["model"]
            score = rec["score"]

            intel_color = (
                "green"
                if m.intelligence >= 80
                else "yellow"
                if m.intelligence >= 50
                else "white"
            )
            intel_str = f"[{intel_color}]{m.intelligence:.0f}[/{intel_color}]"
            speed_str = f"{m.speed_tps:.0f} tps" if m.speed_tps > 0 else "—"

            if m.local:
                price_str = "[green]FREE[/green]"
            else:
                price_str = f"${m.output_per_mtok:.2f}"

            table.add_row(
                str(i),
                f"{score:.1f}",
                m.id,
                m.provider,
                intel_str,
                speed_str,
                price_str,
            )

        console.print(table)

        # Hardware hint
        vram_str = f", {sys_profile.vram_gb:.1f}GB VRAM" if sys_profile.vram_gb else ""
        console.print(
            f"\n[dim]Hardware used for filtering: {sys_profile.ram_gb:.1f}GB RAM{vram_str} ({sys_profile.gpu_kind or 'CPU'})[/dim]"
        )

    asyncio.run(_async_recommend())
