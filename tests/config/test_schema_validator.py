"""Tests for routing config schema validation."""

from __future__ import annotations

import pytest

from harnessctl.config.schema_validator import (
    RoutingConfigSchemaError,
    validate_routing_config_document,
)


def _valid_routing_config() -> dict[str, object]:
    return {
        "apiVersion": "harnessctl/v1alpha1",
        "kind": "RoutingConfig",
        "metadata": {"name": "default"},
        "spec": {
            "taxonomy": {},
            "agent_registry": {},
            "routing": {},
            "escalation": {},
        },
    }


def test_valid_document_passes() -> None:
    validate_routing_config_document(_valid_routing_config())


def test_missing_api_version_fails() -> None:
    doc = _valid_routing_config()
    doc.pop("apiVersion")
    with pytest.raises(
        RoutingConfigSchemaError, match="Missing required field: apiVersion"
    ):
        validate_routing_config_document(doc)


def test_unsupported_api_version_fails() -> None:
    doc = _valid_routing_config()
    doc["apiVersion"] = "harnessctl/v2"
    with pytest.raises(RoutingConfigSchemaError, match="Unsupported apiVersion"):
        validate_routing_config_document(doc)


def test_missing_required_top_level_field_fails() -> None:
    doc = _valid_routing_config()
    doc.pop("kind")
    with pytest.raises(
        RoutingConfigSchemaError,
        match=r"Schema validation failed: 'kind' is a required property",
    ):
        validate_routing_config_document(doc)


def test_missing_required_spec_field_fails() -> None:
    doc = _valid_routing_config()
    spec = dict(doc["spec"])  # type: ignore[arg-type]
    spec.pop("routing")
    doc["spec"] = spec
    with pytest.raises(
        RoutingConfigSchemaError,
        match=r"Schema validation failed at 'spec': 'routing' is a required property",
    ):
        validate_routing_config_document(doc)


def test_invalid_kind_const_fails() -> None:
    doc = _valid_routing_config()
    doc["kind"] = "OtherConfig"
    with pytest.raises(
        RoutingConfigSchemaError,
        match=r"Schema validation failed at 'kind': 'RoutingConfig' was expected",
    ):
        validate_routing_config_document(doc)


def test_null_metadata_name_fails() -> None:
    doc = _valid_routing_config()
    doc["metadata"] = {"name": None}
    with pytest.raises(
        RoutingConfigSchemaError,
        match=r"Schema validation failed at 'metadata\.name': None is not of type 'string'",
    ):
        validate_routing_config_document(doc)
