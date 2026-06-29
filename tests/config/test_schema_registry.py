"""Tests for versioned routing schema registry."""

from __future__ import annotations

import pytest

from harnessctl.config.schema_registry import get_schema_path_for_api_version


def test_resolves_known_v1alpha1_schema_path() -> None:
    schema_path = get_schema_path_for_api_version("harnessctl/v1alpha1")
    assert schema_path.name == "harnessctl-v1alpha1-routing.schema.json"
    assert schema_path.is_file()
    assert schema_path.parent.name == "config"
    assert schema_path.parent.parent.name == "schemas"


def test_raises_for_unknown_api_version() -> None:
    with pytest.raises(ValueError, match="Unsupported apiVersion"):
        get_schema_path_for_api_version("harnessctl/v9")
