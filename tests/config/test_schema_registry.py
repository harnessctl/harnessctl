"""Tests for versioned routing schema registry."""

from __future__ import annotations

from pathlib import Path

import pytest

from harnessctl.config import schema_registry
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


def test_uses_packaged_schema_when_available(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    schema_name = "harnessctl-v1alpha1-routing.schema.json"
    package_dir = tmp_path / "packaged"
    source_dir = tmp_path / "source"
    package_dir.mkdir()
    source_dir.mkdir()
    (package_dir / schema_name).write_text("{}", encoding="utf-8")
    (source_dir / schema_name).write_text("{}", encoding="utf-8")

    monkeypatch.setattr(
        schema_registry, "_package_schema_base_dir", lambda: package_dir
    )
    monkeypatch.setattr(schema_registry, "_source_schema_base_dir", lambda: source_dir)

    resolved = get_schema_path_for_api_version("harnessctl/v1alpha1")
    assert resolved == package_dir / schema_name


def test_falls_back_to_source_schema_when_packaged_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    schema_name = "harnessctl-v1alpha1-routing.schema.json"
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / schema_name).write_text("{}", encoding="utf-8")

    monkeypatch.setattr(schema_registry, "_package_schema_base_dir", lambda: None)
    monkeypatch.setattr(schema_registry, "_source_schema_base_dir", lambda: source_dir)

    resolved = get_schema_path_for_api_version("harnessctl/v1alpha1")
    assert resolved == source_dir / schema_name
