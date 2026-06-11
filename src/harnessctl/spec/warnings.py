from dataclasses import dataclass


@dataclass
class Warning:
    harness: str | None
    field: str
    reason: str
    fallback: str | None = None


class WarningCollector:
    """Collects and aggregates warnings during spec load and emit phases."""

    def __init__(self) -> None:
        self.warnings: list[Warning] = []

    def add(
        self,
        field: str,
        reason: str,
        harness: str | None = None,
        fallback: str | None = None,
    ) -> None:
        self.warnings.append(
            Warning(harness=harness, field=field, reason=reason, fallback=fallback)
        )

    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    def print_warnings(self) -> None:
        # Simplistic console output for now
        for w in self.warnings:
            h_prefix = f"[{w.harness}] " if w.harness else ""
            fb_suffix = f" (fallback: {w.fallback})" if w.fallback else ""
            print(f"WARN: {h_prefix}{w.field} - {w.reason}{fb_suffix}")
