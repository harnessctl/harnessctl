"""Tests for harnessctl.spec.loader."""

from pathlib import Path


from harnessctl.spec.loader import _deep_merge, _load_yaml, load_spec


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
