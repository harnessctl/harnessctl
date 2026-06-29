"""Validation for routing config documents against versioned JSON schemas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from harnessctl.config.schema_registry import get_schema_path_for_api_version


class RoutingConfigSchemaError(Exception):
    """Raised when a routing config fails schema validation."""


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
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


def _validate_required_fields(
    document: dict[str, Any], schema: dict[str, Any], *, field_name: str
) -> None:
    required = schema.get("required", [])
    if not isinstance(required, list):
        raise RoutingConfigSchemaError(
            f"Schema field {field_name}.required must be a list"
        )

    missing = [field for field in required if field not in document]
    if missing:
        missing_str = ", ".join(sorted(str(field) for field in missing))
        raise RoutingConfigSchemaError(
            f"Missing required field(s) in {field_name}: {missing_str}"
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
    _validate_required_fields(routing_document, schema, field_name="document")

    spec_schema = schema.get("properties", {}).get("spec")
    if isinstance(spec_schema, dict):
        spec_value = routing_document.get("spec")
        if spec_value is None:
            return
        spec_object = _require_object(spec_value, field_name="spec")
        _validate_required_fields(spec_object, spec_schema, field_name="spec")
