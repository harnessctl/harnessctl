"""Tests for harnessctl.render.engine."""

from pathlib import Path

import jinja2
import pytest

from harnessctl.render.engine import RenderEngine
from harnessctl.spec.models import (
    HarnessCapabilities,
    HarnessTarget,
    Spec,
    Tier,
)


class TestHarnessCapabilitiesInTemplates:
    def test_supports_mcp_conditional(self, tmp_path: Path) -> None:
        tmpl_dir = tmp_path / "tmpl"
        tmpl_dir.mkdir()
        (tmpl_dir / "test.j2").write_text(
            "{% if harness.supports_mcp %}mcp{% else %}no-mcp{% endif %}"
        )

        spec = Spec(
            harness={
                "h1": HarnessTarget(
                    capabilities=HarnessCapabilities(supports_mcp=True)
                ),
            },
        )
        engine = RenderEngine([tmpl_dir]).bind_spec(spec)
        ctx = {"harness": type("H", (), {"supports_mcp": True})()}
        result = engine.render("test.j2", ctx)
        assert result == "mcp"

    def test_supports_mcp_false(self, tmp_path: Path) -> None:
        tmpl_dir = tmp_path / "tmpl"
        tmpl_dir.mkdir()
        (tmpl_dir / "test.j2").write_text(
            "{% if harness.supports_mcp %}mcp{% else %}no-mcp{% endif %}"
        )

        spec = Spec(
            harness={
                "h1": HarnessTarget(
                    capabilities=HarnessCapabilities(supports_mcp=False)
                ),
            },
        )
        engine = RenderEngine([tmpl_dir]).bind_spec(spec)
        ctx = {"harness": type("H", (), {"supports_mcp": False})()}
        result = engine.render("test.j2", ctx)
        assert result == "no-mcp"


class TestModelRefFilter:
    def test_model_ref_resolves_primary(self, tmp_path: Path) -> None:
        tmpl_dir = tmp_path / "tmpl"
        tmpl_dir.mkdir()
        (tmpl_dir / "test.j2").write_text("{{ 'basic' | model_ref }}")

        spec = Spec(
            tiers={"basic": Tier(primary="gpt-4o")},
        )
        engine = RenderEngine([tmpl_dir]).bind_spec(spec)
        result = engine.render("test.j2", {})
        assert result == "gpt-4o"

    def test_tier_model_alias(self, tmp_path: Path) -> None:
        tmpl_dir = tmp_path / "tmpl"
        tmpl_dir.mkdir()
        (tmpl_dir / "test.j2").write_text("{{ 'basic' | tier_model }}")

        spec = Spec(
            tiers={"basic": Tier(primary="gpt-4o")},
        )
        engine = RenderEngine([tmpl_dir]).bind_spec(spec)
        result = engine.render("test.j2", {})
        assert result == "gpt-4o"

    def test_model_ref_missing_tier_raises(self, tmp_path: Path) -> None:
        tmpl_dir = tmp_path / "tmpl"
        tmpl_dir.mkdir()
        (tmpl_dir / "test.j2").write_text("{{ 'missing' | model_ref }}")

        spec = Spec()
        engine = RenderEngine([tmpl_dir]).bind_spec(spec)
        with pytest.raises(
            jinja2.TemplateRuntimeError, match="Tier 'missing' not found"
        ):
            engine.render("test.j2", {})

    def test_template_not_found(self, tmp_path: Path) -> None:
        engine = RenderEngine([tmp_path]).bind_spec(Spec())
        with pytest.raises(jinja2.TemplateNotFound):
            engine.render("nope.j2", {})
