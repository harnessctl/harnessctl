import typer
from harnessctl.pricing.catalog import MarketModel


def filter_options():
    """Shared filter options for Typer commands."""
    return {
        "min_intel": typer.Option(0, "--min-intel", help="Min intelligence (0-100)."),
        "max_intel": typer.Option(100, "--max-intel", help="Max intelligence (0-100)."),
        "min_speed": typer.Option(0, "--min-speed", help="Min speed (TPS)."),
        "max_speed": typer.Option(float("inf"), "--max-speed", help="Max speed (TPS)."),
        "min_price": typer.Option(
            0, "--min-price", help="Min price per MTok (output)."
        ),
        "max_price": typer.Option(
            float("inf"), "--max-price", help="Max price per MTok (output)."
        ),
        "min_context": typer.Option(0, "--min-context", help="Min context window."),
        "max_context": typer.Option(
            2**31 - 1, "--max-context", help="Max context window."
        ),
    }


def apply_filters(
    catalog: list[MarketModel],
    min_intel: float = 0,
    max_intel: float = 100,
    min_speed: float = 0,
    max_speed: float = float("inf"),
    min_price: float = 0,
    max_price: float = float("inf"),
    min_context: int = 0,
    max_context: int = 2**31 - 1,
) -> list[MarketModel]:
    """Apply standard filters to a model catalog."""
    return [
        m
        for m in catalog
        if min_intel <= m.intelligence <= max_intel
        and min_speed <= m.speed_tps <= max_speed
        and min_price <= m.output_per_mtok <= max_price
        and min_context <= m.context_window <= max_context
    ]
