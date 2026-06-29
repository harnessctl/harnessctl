"""Validation for routing config documents against versioned JSON schemas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

from harnessctl.config.schema_registry import get_schema_path_for_api_version


class RoutingConfigSchemaError(Exception):
    """Raised when a routing config fails schema validation."""


def _load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except OSError as exc:
        raise RoutingConfigSchemaError(
            f"Failed to read schema file at {path}: {exc}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise RoutingConfigSchemaError(
            f"Failed to parse schema JSON at {path}: {exc.msg}"
        ) from exc

    if not isinstance(data, dict):
        raise RoutingConfigSchemaError(
            f"Schema file must contain a JSON object: {path}"
        )
    return data


def _require_object(value: Any, *, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RoutingConfigSchemaError(
            f"Routing config must be an object; got {type(value).__name__}"
        )
    return value


def _format_validation_error(error: ValidationError | SchemaError) -> str:
    if error.path:
        path = ".".join(str(part) for part in error.path)
        return f"Schema validation failed at '{path}': {error.message}"
    return f"Schema validation failed: {error.message}"


def _validate_agent_registry_semantics(document: dict[str, Any]) -> None:
    """Validate semantic constraints not expressible in base JSON schema."""
    spec = document.get("spec")
    if not isinstance(spec, dict):
        return

    registry = spec.get("agent_registry")
    if not isinstance(registry, dict):
        return

    agents = registry.get("agents")
    if not isinstance(agents, list):
        return

    seen_agent_ids: set[str] = set()
    duplicate_ids: set[str] = set()
    for agent in agents:
        if not isinstance(agent, dict):
            continue
        agent_id = agent.get("id")
        if not isinstance(agent_id, str) or not agent_id:
            continue
        if agent_id in seen_agent_ids:
            duplicate_ids.add(agent_id)
        seen_agent_ids.add(agent_id)

    if duplicate_ids:
        duplicates = ", ".join(sorted(duplicate_ids))
        raise RoutingConfigSchemaError(
            "Schema validation failed at 'spec.agent_registry.agents': "
            f"duplicate agent id(s): {duplicates}"
        )


def validate_routing_config_document(document: dict[str, Any]) -> None:
    """Validate routing config document against mapped versioned schema.

    This v1 implementation validates top-level required keys deterministically,
    using the `apiVersion` -> schema artifact mapping.
    """
    routing_document = _require_object(document, field_name="document")
    api_version = routing_document.get("apiVersion")
    if not isinstance(api_version, str) or not api_version.strip():
        raise RoutingConfigSchemaError("Missing required field: apiVersion")

    try:
        schema_path = get_schema_path_for_api_version(api_version)
    except ValueError as exc:
        raise RoutingConfigSchemaError(str(exc)) from exc

    schema = _load_json(schema_path)
    try:
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(routing_document)
        _validate_agent_registry_semantics(routing_document)
    except SchemaError as exc:
        raise RoutingConfigSchemaError(_format_validation_error(exc)) from exc
    except ValidationError as exc:
        raise RoutingConfigSchemaError(_format_validation_error(exc)) from exc
