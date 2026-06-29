import json
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
from harnessctl.routing import (
    PolicyGateError,
    apply_policy_gates,
    build_fallback_chain,
    derive_task_metadata,
    select_primary_candidate,
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


def _load_request_payload(
    *,
    request_json: str | None,
    request_file: Path | None,
) -> dict[str, object]:
    if (request_json is None) == (request_file is None):
        typer.secho(
            "You must provide exactly one of --request-json or --request-file.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=2)

    raw_payload: str
    if request_json is not None:
        raw_payload = request_json
    else:
        assert request_file is not None
        if not request_file.exists():
            typer.secho(f"Request file not found: {request_file}", fg=typer.colors.RED)
            raise typer.Exit(code=2)
        raw_payload = request_file.read_text(encoding="utf-8")

    try:
        parsed = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        typer.secho(f"Invalid JSON request payload: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=2) from exc

    if not isinstance(parsed, dict):
        typer.secho("Request payload must be a JSON object.", fg=typer.colors.RED)
        raise typer.Exit(code=2)

    return parsed


def _load_routing_config(config_file: Path | None) -> dict[str, object]:
    path = config_file
    if path is None:
        path = get_global_config_base_dir() / "config.yaml"
    if not path.exists():
        typer.secho(f"Config file not found: {path}", fg=typer.colors.RED)
        raise typer.Exit(code=2)

    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        typer.secho(f"Invalid YAML in config file: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=2) from exc

    if not isinstance(loaded, dict):
        typer.secho("Config file must contain a YAML object.", fg=typer.colors.RED)
        raise typer.Exit(code=2)

    try:
        validate_routing_config_document(loaded)
    except RoutingConfigSchemaError as exc:
        typer.secho(f"Config validation failed: {exc}", fg=typer.colors.RED)
        raise typer.Exit(code=2) from exc

    return loaded


def _matching_rule_names(
    *,
    request: dict[str, object],
    derived: dict[str, object],
    routing_config: dict[str, object],
) -> list[str]:
    spec = routing_config.get("spec") if isinstance(routing_config, dict) else None
    if not isinstance(spec, dict):
        return []
    routing = spec.get("routing")
    if not isinstance(routing, dict):
        return []
    rules = routing.get("rules")
    if not isinstance(rules, list):
        return []

    task_type = (
        str(request.get("task_type") or derived.get("task_class") or "").strip().lower()
    )
    complexity = derived.get("complexity")
    complexity_value = complexity if isinstance(complexity, (int, float)) else None

    matched: list[str] = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        name = rule.get("name")
        when = rule.get("when")
        if not isinstance(name, str) or not isinstance(when, dict):
            continue

        task_ok = True
        allowed = when.get("task_type_in")
        if isinstance(allowed, list) and allowed:
            allowed_set = {
                str(value).strip().lower()
                for value in allowed
                if isinstance(value, str) and str(value).strip()
            }
            task_ok = task_type in allowed_set

        complexity_ok = True
        max_complexity = when.get("max_complexity")
        if isinstance(max_complexity, (int, float)) and complexity_value is not None:
            complexity_ok = complexity_value <= max_complexity

        if task_ok and complexity_ok:
            matched.append(name)
    return matched


def _resolve_scoring_objective(
    *,
    routing_config: dict[str, object],
    matched_rule_names: list[str],
) -> str:
    default_objective = "cost_per_success"
    if not matched_rule_names:
        return default_objective

    spec = routing_config.get("spec") if isinstance(routing_config, dict) else None
    routing = spec.get("routing") if isinstance(spec, dict) else None
    rules = routing.get("rules") if isinstance(routing, dict) else None
    if not isinstance(rules, list):
        return default_objective

    for target_name in matched_rule_names:
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            if rule.get("name") != target_name:
                continue
            choose = rule.get("choose")
            if not isinstance(choose, dict):
                continue
            objective = choose.get("optimize_for")
            if isinstance(objective, str):
                normalized = objective.strip().lower()
                if normalized in {"cost", "cost_per_success"}:
                    return normalized
    return default_objective


def _estimate_cost_usd_from_agent(agent: dict[str, object]) -> float | None:
    cost = agent.get("cost")
    if not isinstance(cost, dict):
        return None
    direct = cost.get("estimated_cost_usd")
    if isinstance(direct, (int, float)) and direct >= 0:
        return float(direct)
    return None


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
def mcp_select_model_for_task_command(
    request_json: Optional[str] = typer.Option(
        None,
        "--request-json",
        help="Inline JSON request payload for model selection.",
    ),
    request_file: Optional[Path] = typer.Option(
        None,
        "--request-file",
        help="Path to JSON request payload file.",
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config-file",
        help="Path to routing config YAML (defaults to ~/.config/harnessctl/config.yaml).",
    ),
    pretty: bool = typer.Option(
        False,
        "--pretty",
        help="Pretty-print JSON response.",
    ),
) -> None:
    """MCP model selection entrypoint with agent-first response contract."""
    request = _load_request_payload(
        request_json=request_json, request_file=request_file
    )
    routing_config = _load_routing_config(config_file)

    derived_payload = derive_task_metadata(request, routing_config=routing_config)
    derived = derived_payload.get("derived")
    provenance = derived_payload.get("provenance")
    if not isinstance(derived, dict) or not isinstance(provenance, dict):
        typer.secho("Derived routing metadata is malformed.", fg=typer.colors.RED)
        raise typer.Exit(code=2)

    matched_rules = _matching_rule_names(
        request=request,
        derived=derived,
        routing_config=routing_config,
    )
    objective = _resolve_scoring_objective(
        routing_config=routing_config,
        matched_rule_names=matched_rules,
    )

    try:
        policy_result = apply_policy_gates(
            request,
            derived_metadata=derived_payload,
            routing_config=routing_config,
        )
        candidates = policy_result["candidates"]
        policy_checks = policy_result["policy_checks"]
        scoring = select_primary_candidate(
            request=request,
            candidates=candidates,
            objective=objective,
        )
        selected_agent = scoring["selected_agent"]
        selected_agent_id = scoring["selected_agent_id"]
        fallback = build_fallback_chain(
            request=request,
            derived_metadata=derived_payload,
            routing_config=routing_config,
            candidates=candidates,
            selected_agent_id=selected_agent_id,
        )

        selected_model = str(selected_agent.get("model") or "")
        selected_provider = str(selected_agent.get("provider") or "")
        selected_tier = str(selected_agent.get("tier") or "")

        response: dict[str, object] = {
            "selected_agent": selected_agent_id,
            "selected_model": selected_model,
            "selected_provider": selected_provider,
            "selected_tier": selected_tier,
            "reason": (
                f"Matched {len(matched_rules)} routing rule(s) and selected by "
                f"{scoring['selection_strategy']}."
            ),
            "confidence": 0.8
            if scoring["ranked_candidates"][0]["score"] is not None
            else 0.6,
            "estimated_cost_usd": _estimate_cost_usd_from_agent(selected_agent),
            "fallback_agents": fallback["fallback_agents"],
            "trace": {
                "policy_checks": policy_checks,
                "matched_rules": matched_rules,
                "candidates_considered": len(candidates),
                "selection_strategy": scoring["selection_strategy"],
                "derived": derived,
                "provenance": provenance,
                "chain_name": fallback["chain_name"],
                "escalation_action": fallback["escalation_action"],
                "tier_sequence": fallback["tier_sequence"],
                "matched_keyword_override": fallback["matched_keyword_override"],
            },
        }
    except PolicyGateError as exc:
        response = {
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
            "trace": {
                "derived": derived,
                "provenance": provenance,
            },
        }

    typer.echo(json.dumps(response, indent=2 if pretty else None, sort_keys=False))


@app.command()
def version():
    """Show the version of harnessctl."""
    typer.echo("harnessctl 0.1.0")


def run():
    app()


if __name__ == "__main__":
    run()
