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
            "agent_registry": {
                "agents": [
                    {
                        "id": "agent-default",
                        "model": "github-copilot/gpt-5-mini",
                        "provider": "github-copilot",
                        "tier": "strong",
                        "capabilities": ["implementation", "review"],
                    }
                ]
            },
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


def test_missing_agent_required_field_fails() -> None:
    doc = _valid_routing_config()
    agents = doc["spec"]["agent_registry"]["agents"]  # type: ignore[index]
    agents[0].pop("model")  # type: ignore[index]
    with pytest.raises(
        RoutingConfigSchemaError,
        match=r"Schema validation failed at 'spec\.agent_registry\.agents\.0': 'model' is a required property",
    ):
        validate_routing_config_document(doc)


def test_rejects_duplicate_agent_ids() -> None:
    doc = _valid_routing_config()
    agents = doc["spec"]["agent_registry"]["agents"]  # type: ignore[index]
    agents.append(agents[0].copy())  # type: ignore[union-attr]
    with pytest.raises(
        RoutingConfigSchemaError,
        match=r"duplicate agent id\(s\): agent-default",
    ):
        validate_routing_config_document(doc)


def test_rejects_empty_agent_registry() -> None:
    doc = _valid_routing_config()
    doc["spec"]["agent_registry"]["agents"] = []  # type: ignore[index]
    with pytest.raises(
        RoutingConfigSchemaError,
        match=r"Schema validation failed at 'spec\.agent_registry\.agents': \[\] should be non-empty",
    ):
        validate_routing_config_document(doc)


def test_rejects_invalid_agent_tier() -> None:
    doc = _valid_routing_config()
    agents = doc["spec"]["agent_registry"]["agents"]  # type: ignore[index]
    agents[0]["tier"] = "ultra"  # type: ignore[index]
    with pytest.raises(
        RoutingConfigSchemaError,
        match=r"Schema validation failed at 'spec\.agent_registry\.agents\.0\.tier': 'ultra' is not one of",
    ):
        validate_routing_config_document(doc)


def test_rejects_malformed_agent_capabilities() -> None:
    doc = _valid_routing_config()
    agents = doc["spec"]["agent_registry"]["agents"]  # type: ignore[index]
    agents[0]["capabilities"] = ["implementation", "implementation"]  # type: ignore[index]
    with pytest.raises(
        RoutingConfigSchemaError,
        match=r"Schema validation failed at 'spec\.agent_registry\.agents\.0\.capabilities': \['implementation', 'implementation'\] has non-unique elements",
    ):
        validate_routing_config_document(doc)


def test_rejects_whitespace_only_agent_fields() -> None:
    doc = _valid_routing_config()
    agents = doc["spec"]["agent_registry"]["agents"]  # type: ignore[index]
    agents[0]["id"] = "   "  # type: ignore[index]
    with pytest.raises(
        RoutingConfigSchemaError,
        match=r"Schema validation failed at 'spec\.agent_registry\.agents\.0\.id': '   ' does not match",
    ):
        validate_routing_config_document(doc)


def test_accepts_valid_agent_cost_band() -> None:
    doc = _valid_routing_config()
    agents = doc["spec"]["agent_registry"]["agents"]  # type: ignore[index]
    agents[0]["cost_band"] = "premium"  # type: ignore[index]
    validate_routing_config_document(doc)


def test_rejects_invalid_agent_cost_band() -> None:
    doc = _valid_routing_config()
    agents = doc["spec"]["agent_registry"]["agents"]  # type: ignore[index]
    agents[0]["cost_band"] = "ultra-cheap"  # type: ignore[index]
    with pytest.raises(
        RoutingConfigSchemaError,
        match=r"Schema validation failed at 'spec\.agent_registry\.agents\.0\.cost_band': 'ultra-cheap' is not one of",
    ):
        validate_routing_config_document(doc)
