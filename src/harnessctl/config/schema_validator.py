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
    except SchemaError as exc:
        raise RoutingConfigSchemaError(_format_validation_error(exc)) from exc
    except ValidationError as exc:
        raise RoutingConfigSchemaError(_format_validation_error(exc)) from exc
