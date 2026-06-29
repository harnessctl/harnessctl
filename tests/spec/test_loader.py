"""Tests for harnessctl.spec.loader."""

from pathlib import Path

import pytest


from harnessctl.spec.loader import _deep_merge, _load_yaml, _merge_keyed_list, load_spec


class TestDeepMerge:
    def test_empty_dicts(self) -> None:
        assert _deep_merge({}, {}) == {}

    def test_override_scalar(self) -> None:
        assert _deep_merge({"a": 1}, {"a": 2}) == {"a": 2}

    def test_override_list(self) -> None:
        """Lists must replace, not append."""
        assert _deep_merge({"a": [1, 2]}, {"a": [3]}) == {"a": [3]}

    def test_nested_dict_merge(self) -> None:
        base = {"x": {"a": 1, "b": 2}}
        override = {"x": {"b": 3, "c": 4}}
        assert _deep_merge(base, override) == {"x": {"a": 1, "b": 3, "c": 4}}

    def test_add_new_keys(self) -> None:
        assert _deep_merge({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}

    def test_replace_dict_with_scalar(self) -> None:
        assert _deep_merge({"a": {"b": 1}}, {"a": 2}) == {"a": 2}

    def test_replace_scalar_with_dict(self) -> None:
        assert _deep_merge({"a": 1}, {"a": {"b": 2}}) == {"a": {"b": 2}}

    def test_keyed_list_merge_by_id(self) -> None:
        base = {
            "agents": [
                {"id": "hub", "tier": "cheap", "capabilities": ["implementation"]},
                {"id": "worker", "tier": "medium", "capabilities": ["review"]},
            ]
        }
        override = {
            "agents": [
                {"id": "hub", "tier": "strong"},
                {"id": "new", "tier": "reasoning", "capabilities": ["design"]},
            ]
        }
        merged = _deep_merge(base, override)
        assert merged["agents"] == [
            {"id": "hub", "tier": "strong", "capabilities": ["implementation"]},
            {"id": "worker", "tier": "medium", "capabilities": ["review"]},
            {"id": "new", "tier": "reasoning", "capabilities": ["design"]},
        ]

    def test_keyed_list_merge_by_name(self) -> None:
        base = {"rules": [{"name": "r1", "enabled": True}]}
        override = {"rules": [{"name": "r1", "enabled": False}]}
        merged = _deep_merge(base, override)
        assert merged["rules"] == [{"name": "r1", "enabled": False}]

    def test_keyed_list_fallback_replace_when_identity_missing(self) -> None:
        base = {"agents": [{"id": "hub", "tier": "cheap"}]}
        override = {"agents": [{"tier": "strong"}]}
        merged = _deep_merge(base, override)
        assert merged["agents"] == [{"tier": "strong"}]


class TestLoadYaml:
    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert _load_yaml(tmp_path / "nope.yaml") == {}

    def test_loads_simple_yaml(self, tmp_path: Path) -> None:
        path = tmp_path / "test.yaml"
        path.write_text("version: '1.0'\n")
        assert _load_yaml(path) == {"version": "1.0"}

    def test_non_dict_yaml_returns_empty(self, tmp_path: Path) -> None:
        path = tmp_path / "list.yaml"
        path.write_text("- a\n- b\n")
        assert _load_yaml(path) == {}


class TestLoadSpec:
    def test_single_file(self, tmp_path: Path) -> None:
        path = tmp_path / "config.yaml"
        path.write_text("version: '2.0'\n")
        spec = load_spec(defaults_path=path)
        assert spec.version == "2.0"

    def test_precedence_defaults_overridden_by_user(self, tmp_path: Path) -> None:
        defaults = tmp_path / "defaults.yaml"
        defaults.write_text("version: '1.0'\ntiers:\n  basic:\n    primary: m1\n")

        user = tmp_path / "user.yaml"
        user.write_text("version: '2.0'\n")

        spec = load_spec(defaults_path=defaults, user_config_path=user)
        assert spec.version == "2.0"
        assert "basic" in spec.tiers

    def test_precedence_project_over_user(self, tmp_path: Path) -> None:
        user = tmp_path / "user.yaml"
        user.write_text("version: '1.0'\n")

        project = tmp_path / "project.yaml"
        project.write_text("version: '3.0'\n")

        spec = load_spec(user_config_path=user, project_local_path=project)
        assert spec.version == "3.0"

    def test_precedence_cli_over_all(self, tmp_path: Path) -> None:
        defaults = tmp_path / "defaults.yaml"
        defaults.write_text("version: '1.0'\n")

        spec = load_spec(defaults_path=defaults, cli_overrides={"version": "4.0"})
        assert spec.version == "4.0"

    def test_deep_merge_maps(self, tmp_path: Path) -> None:
        defaults = tmp_path / "defaults.yaml"
        defaults.write_text("tiers:\n  basic:\n    primary: m1\n    fallback: m2\n")
        user = tmp_path / "user.yaml"
        user.write_text("tiers:\n  basic:\n    fallback: m3\n")

        spec = load_spec(defaults_path=defaults, user_config_path=user)
        assert spec.tiers["basic"].primary == "m1"
        assert spec.tiers["basic"].fallback == "m3"

    def test_lists_replace(self, tmp_path: Path) -> None:
        defaults = tmp_path / "defaults.yaml"
        defaults.write_text(
            "agents:\n  a1:\n    tier: basic\n    role: hub\n    can_delegate:\n      - m1\n"
        )
        user = tmp_path / "user.yaml"
        user.write_text(
            "agents:\n  a1:\n    tier: basic\n    role: hub\n    can_delegate:\n      - m2\n"
        )

        spec = load_spec(defaults_path=defaults, user_config_path=user)
        assert spec.agents["a1"].can_delegate == ["m2"]

    def test_lists_non_keyed_replace(self, tmp_path: Path) -> None:
        defaults = tmp_path / "defaults.yaml"
        defaults.write_text("profiles:\n  p1:\n    budget_limit: 1.0\n")
        user = tmp_path / "user.yaml"
        user.write_text("profiles:\n  p1:\n    budget_limit: 2.5\n")

        spec = load_spec(defaults_path=defaults, user_config_path=user)
        assert spec.profiles["p1"].budget_limit == 2.5

    def test_precedence_runtime_over_project_over_global_over_defaults(
        self, tmp_path: Path
    ) -> None:
        defaults = tmp_path / "defaults.yaml"
        defaults.write_text("version: '1.0'\n")

        global_cfg = tmp_path / "global.yaml"
        global_cfg.write_text("version: '2.0'\n")

        project_cfg = tmp_path / "project.yaml"
        project_cfg.write_text("version: '3.0'\n")

        spec = load_spec(
            defaults_path=defaults,
            user_config_path=global_cfg,
            project_local_path=project_cfg,
            cli_overrides={"version": "4.0"},
        )
        assert spec.version == "4.0"


class TestMergeKeyedList:
    def test_merge_preserves_order_and_applies_updates(self) -> None:
        base = [{"id": "a", "x": 1}, {"id": "b", "x": 2}]
        override = [{"id": "a", "y": 3}, {"id": "c", "x": 4}]
        merged = _merge_keyed_list(base, override)
        assert merged == [
            {"id": "a", "x": 1, "y": 3},
            {"id": "b", "x": 2},
            {"id": "c", "x": 4},
        ]

    def test_duplicate_identities_in_base_raise(self) -> None:
        with pytest.raises(ValueError, match="Duplicate keyed-list identities"):
            _merge_keyed_list(
                [{"id": "a", "x": 1}, {"id": "a", "x": 2}],
                [{"id": "a", "x": 3}],
            )

    def test_non_string_identity_falls_back_to_override(self) -> None:
        merged = _merge_keyed_list(
            [{"id": "a", "x": 1}],
            [{"id": 1, "x": 2}],
        )
        assert merged == [{"id": 1, "x": 2}]

    def test_chains_field_uses_keyed_merge(self) -> None:
        merged = _deep_merge(
            {"chains": [{"name": "default", "steps": ["cheap", "medium"]}]},
            {"chains": [{"name": "default", "steps": ["strong"]}]},
        )
        assert merged["chains"] == [{"name": "default", "steps": ["strong"]}]

    def test_missing_files_skipped(self, tmp_path: Path) -> None:
        """Ensure missing intermediate files don't break loading."""
        project = tmp_path / "project.yaml"
        project.write_text("version: '1.0'\n")
        spec = load_spec(
            defaults_path=tmp_path / "missing.yaml",
            user_config_path=tmp_path / "also_missing.yaml",
            project_local_path=project,
        )
        assert spec.version == "1.0"
