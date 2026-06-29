import asyncio
import typer
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel

from harnessctl.discovery.probes import discover_all
from harnessctl.discovery.status import get_all_services_status, ServiceStatus
from harnessctl.pricing.market import fetch_market_data
from harnessctl.pricing.catalog import merge_market_data, MarketModel
from harnessctl.discovery.base import run_probes
from harnessctl.discovery.ollama import OllamaProbe
from harnessctl.discovery.mlx import MLXProbe
from harnessctl.discovery.openai_compat import OpenAICompatProbe
from harnessctl.discovery.opencode import OpencodeProbe
from harnessctl.commands.utils import apply_filters

console = Console()
models_app = typer.Typer(help="Manage and discover models.")


async def _get_local_models() -> List:
    probes = [
        OllamaProbe(),
        MLXProbe(),
        OpenAICompatProbe(runtime="lmstudio", endpoint="http://localhost:1234/v1"),
        OpencodeProbe(),
    ]
    return await run_probes(probes)


@models_app.command(name="providers")
def list_providers_cmd(
    ctx: typer.Context,
    refresh: bool = typer.Option(
        False, "--refresh", help="Force refresh market data from registry."
    ),
):
    """List available model providers and their model counts."""

    async def _async_list():
        warnings = ctx.obj.warnings

        with console.status("[bold green]Fetching provider registry..."):
            market_models = await fetch_market_data(warnings, force_refresh=refresh)

        # Count models per provider
        from collections import Counter

        counts = Counter(m.provider for m in market_models)

        # Provider mappings for "inventive" metadata (URLs)
        # Note: In a real app, this could be a registry. For now, we heuristic-map common ones.
        provider_urls = {
            "openai": "https://openai.com",
            "anthropic": "https://anthropic.com",
            "google": "https://ai.google.dev",
            "vertex": "https://cloud.google.com/vertex-ai",
            "mistral": "https://mistral.ai",
            "cohere": "https://cohere.com",
            "ollama": "https://ollama.com",
            "deepseek": "https://deepseek.com",
            "openrouter": "https://openrouter.ai",
            "groq": "https://groq.com",
            "together": "https://together.ai",
            "fireworks": "https://fireworks.ai",
            "bedrock": "https://aws.amazon.com/bedrock",
            "perplexity": "https://perplexity.ai",
            "xai": "https://x.ai",
            "github": "https://github.com/marketplace/models",
            "github-models": "https://github.com/marketplace/models",
            "copilot": "https://github.com/features/copilot",
            "github-copilot": "https://github.com/features/copilot",
            "abacus": "https://abacus.ai",
        }

        table = Table(title="Model Providers", box=box.ROUNDED)
        table.add_column("Provider ID", style="cyan")
        table.add_column("Models", justify="right", style="green")
        table.add_column("URL", style="blue")

        for provider, count in sorted(counts.items()):
            url = provider_urls.get(provider.lower(), "—")
            # If the provider name is complex (e.g. vertex_ai-anthropic), try to find a base match
            if url == "—":
                for key, val in provider_urls.items():
                    if key in provider.lower():
                        url = val
                        break

            table.add_row(provider, str(count), url)

        console.print(table)
        console.print(
            f"\n[dim]Total: {len(counts)} providers found via registry.[/dim]"
        )

    asyncio.run(_async_list())


def render_catalog_table(title: str, models: List, total_count: Optional[int] = None):
    """Unified table rendering for list and recommend commands."""
    table = Table(
        title=title,
        box=box.ROUNDED,
        caption=f"Showing {len(models)} of {total_count} models"
        if total_count and total_count > len(models)
        else None,
    )

    # Add Score column if it's a recommendation table
    has_score = any(hasattr(m, "score") for m in models)
    if has_score:
        table.add_column("Score", justify="right", style="bold yellow")

    table.add_column("Model ID", style="cyan")
    table.add_column("Provider", style="magenta")
    table.add_column("Intel", justify="right")
    table.add_column("Speed (TPS)", justify="right")
    table.add_column("Price/1M (In/Out)", justify="right")
    table.add_column("Context", justify="right")

    for m in models:
        # Color coding
        intel_val = getattr(m, "intelligence", 0)
        intel_color = (
            "green" if intel_val >= 80 else "yellow" if intel_val >= 50 else "white"
        )

        input_price = getattr(m, "input_per_mtok", 0.0)
        output_price = getattr(m, "output_per_mtok", 0.0)
        price_color = "red" if input_price > 10 else "white"

        # Intelligence Source Indicator
        src_map = {"benchmark": "★", "elo": "○", "heuristic": "≈"}
        intel_src = getattr(m, "intelligence_source", "heuristic")
        src_indicator = src_map.get(intel_src, "")

        intel_str = f"[{intel_color}]{intel_val:.0f}[/{intel_color}]{src_indicator}"

        speed_val = getattr(m, "speed_tps", 0)
        speed_str = f"{speed_val:.0f}" if speed_val > 0 else "—"

        is_local = (
            getattr(m, "local", False)
            or getattr(m, "provider", "").lower() == "huggingface"
        )
        if is_local:
            price_str = "[green]FREE[/green]"
        else:
            price_str = f"[{price_color}]${input_price:.2f} / ${output_price:.2f}[/{price_color}]"

        ctx_val = getattr(m, "context_window", 0)
        ctx_str = f"{ctx_val // 1000}k" if ctx_val >= 1000 else str(ctx_val)

        row = []
        if has_score:
            row.append(f"{getattr(m, 'score', 0):.1f}")

        # In recommend, we might want to show the quant in the ID or name
        model_id = m.id
        if hasattr(m, "quant") and m.quant:
            model_id = f"{model_id} [dim]({m.quant})[/dim]"

        row.extend([model_id, m.provider, intel_str, speed_str, price_str, ctx_str])
        table.add_row(*row)

    console.print(table)


@models_app.command(
    name="list",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def list_cmd(
    ctx: typer.Context,
    local: bool = typer.Option(False, "--local", help="Filter only local models."),
    commercial: bool = typer.Option(
        False, "--commercial", help="Filter only commercial models."
    ),
    sort_by: str = typer.Option(
        "intelligence",
        "--sort-by",
        help="Sort by: field [asc|desc].",
    ),
    provider: Optional[str] = typer.Option(
        None, "--provider", help="Filter by provider (e.g. openai, anthropic, ollama)."
    ),
    grep: Optional[str] = typer.Option(None, "--grep", help="Filter by name."),
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
    min_context: int = typer.Option(0, "--min-context", help="Min context window."),
    max_context: int = typer.Option(
        2**31 - 1, "--max-context", help="Max context window."
    ),
    refresh: bool = typer.Option(False, "--refresh", help="Force refresh market data."),
    reindex: bool = typer.Option(
        False, "--reindex", help="Clear cache and re-probe all services."
    ),
    limit: int = typer.Option(
        50, "--limit", help="Limit number of models displayed (0 for all)."
    ),
    trusted: bool = typer.Option(
        False, "--trusted", help="Filter for official/trusted authors only."
    ),
):
    """List existing models with intelligence, speed and price metrics."""

    # Normalize sort_field and sort_dir
    sort_field = sort_by
    # Default to asc as per user request, but intelligence is usually desc by default
    sort_dir = "desc" if sort_field == "intelligence" else "asc"

    if ctx.args:
        if ctx.args[0].lower() in ["asc", "desc"]:
            sort_dir = ctx.args[0].lower()
            # We don't pop from ctx.args here because Typer might need it for other things
            # or it might cause issues if not handled carefully,
            # but since we have allow_extra_args=True, it's fine.

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

        if trusted:
            from harnessctl.recommend.trusted import is_trusted_author

            catalog = [m for m in catalog if is_trusted_author(m.id)]

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

        # Performance/Price/Context Filtering
        catalog = apply_filters(
            catalog,
            min_intel,
            max_intel,
            min_speed,
            max_speed,
            min_price,
            max_price,
            min_context,
            max_context,
        )

        # 3. Sort
        reverse = sort_dir.lower() == "desc"

        def sort_key(m: MarketModel):
            if sort_field == "intelligence":
                return m.intelligence
            if sort_field == "speed":
                return m.speed_tps
            if sort_field == "price":
                return m.input_per_mtok
            if sort_field == "context":
                return m.context_window
            return m.intelligence

        catalog.sort(key=sort_key, reverse=reverse)

        # 4. Apply display limit
        total_available = len(catalog)
        if limit > 0:
            catalog = catalog[:limit]

        # 5. Render Service Status
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

        # 6. Render Table
        render_catalog_table(
            "Global Model Market & Local Discovery", catalog, total_available
        )

        console.print(
            "\n[dim]Intel Sources: ★ Benchmark (Artificial Analysis), ○ ELO (Design Arena), ≈ Heuristic[/dim]"
        )

        # 7. Print warnings AT THE VERY END (Guaranteed)
        if warnings.has_warnings():
            warning_content = []
            for w in warnings.warnings:
                h_prefix = f"[{w.harness}] " if w.harness else ""
                warning_content.append(
                    f"• [bold yellow]{h_prefix}{w.field}[/bold yellow]: {w.reason}"
                )

            console.print()
            console.print(
                Panel(
                    "\n".join(warning_content),
                    title="[bold yellow]Discovery Warnings[/bold yellow]",
                    border_style="yellow",
                    expand=False,
                )
            )

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


@models_app.command(
    name="recommend",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def recommend_cmd(
    ctx: typer.Context,
    task: str = typer.Argument(
        ..., help="The task description to recommend a model for."
    ),
    local: bool = typer.Option(
        True, "--local/--no-local", help="Include local models."
    ),
    commercial: bool = typer.Option(
        True, "--commercial/--no-commercial", help="Include commercial models."
    ),
    trusted: bool = typer.Option(
        False, "--trusted", help="Filter for official/trusted authors only."
    ),
    provider: Optional[str] = typer.Option(
        None, "--provider", help="Filter by provider."
    ),
    grep: Optional[str] = typer.Option(None, "--grep", help="Filter by name."),
    sort_by: str = typer.Option(
        "score",
        "--sort-by",
        help="Sort by: field [asc|desc].",
    ),
    taxonomy_version: str = typer.Option(
        "latest", "--taxonomy-version", help="Taxonomy version to use."
    ),
    limit: int = typer.Option(10, "--limit", help="Limit number of recommendations."),
):
    """Recommend a model for a specific task based on system hardware."""
    from harnessctl.sysprobe.profile import detect_system
    from harnessctl.recommend.ranker import search_candidates
    from harnessctl.recommend.intent import analyze_intent

    # Normalize sort_field and sort_dir
    sort_field = sort_by
    # Default to asc as per user request, but score/intelligence are usually desc by default
    sort_dir = "desc" if sort_field in ["score", "intelligence"] else "asc"

    if ctx.args:
        if ctx.args[0].lower() in ["asc", "desc"]:
            sort_dir = ctx.args[0].lower()

    profile = detect_system()
    intent = analyze_intent(task, taxonomy_version=taxonomy_version)

    console.print(f"Task: [bold]{task}[/bold]")
    console.print(
        f"Intent: [blue]{'/'.join(intent.domains)}[/blue] | Complexity: [yellow]{intent.complexity}/100[/yellow]"
    )

    vram_str = f"{profile.vram_gb:.1f}GB" if profile.vram_gb else "N/A"
    console.print(f"System: [dim]{profile.ram_gb:.1f}GB RAM, {vram_str} VRAM[/dim]\n")

    async def _async_recommend():
        warnings = ctx.obj.warnings
        market_data = []
        if commercial:
            with console.status("[bold green]Fetching market data..."):
                market_data = await fetch_market_data(warnings)

        if trusted:
            from harnessctl.recommend.trusted import is_trusted_author

            if market_data:
                market_data = [m for m in market_data if is_trusted_author(m.id)]

        with console.status("[bold green]Ranking candidates..."):
            candidates = search_candidates(
                profile,
                intent,
                market_data=market_data,
                include_local=local,
                include_commercial=commercial,
                provider_filter=provider,
                grep=grep,
                limit=limit,
                trusted_only=trusted,
            )

        if not candidates:
            console.print(
                "[yellow]No suitable models found matching your criteria.[/yellow]"
            )
            return

        # 3. Sort if requested (default is score from ranker)
        if sort_field != "score" or sort_dir == "asc":
            reverse = sort_dir.lower() == "desc"

            def sort_key(m):
                if sort_field == "intelligence":
                    return m.intelligence
                if sort_field == "speed":
                    return m.speed_tps
                if sort_field == "price":
                    return m.input_per_mtok
                if sort_field == "context":
                    return m.context_window
                return m.score

            candidates.sort(key=sort_key, reverse=reverse)

        # 4. Apply display limit
        candidates = candidates[:limit]

        render_catalog_table("Model Recommendations", candidates)
        console.print(
            "\n[dim]Intel Sources: ★ Benchmark (Artificial Analysis), ○ ELO (Design Arena), ≈ Heuristic[/dim]"
        )

    asyncio.run(_async_recommend())
