"""Jinja2 rendering engine for harnessctl."""

from pathlib import Path

import jinja2

from harnessctl.spec.models import Spec


def _make_model_ref_filter(spec: Spec):
    """Return a filter that resolves a tier name to its primary model ID."""

    def model_ref(tier_name: str) -> str:
        try:
            tier = spec.tiers[tier_name]
        except KeyError as exc:
            raise jinja2.TemplateRuntimeError(
                f"Tier '{tier_name}' not found in spec."
            ) from exc
        return tier.primary

    return model_ref


class RenderEngine:
    """Jinja2 environment wrapper for harnessctl template rendering."""

    def __init__(self, template_dirs: list[Path]) -> None:
        """Create a new engine loading templates from *template_dirs*.

        Directories are searched in order; the first match wins.
        """
        loaders = [jinja2.FileSystemLoader(str(d)) for d in template_dirs]
        self._env = jinja2.Environment(
            loader=jinja2.ChoiceLoader(loaders),
            autoescape=False,
        )
        self._spec: Spec | None = None

    def bind_spec(self, spec: Spec) -> "RenderEngine":
        """Register *spec* so tier/model filters can resolve references.

        Returns *self* for chaining.
        """
        self._spec = spec
        self._env.filters["model_ref"] = _make_model_ref_filter(spec)
        self._env.filters["tier_model"] = self._env.filters["model_ref"]
        return self

    def render(self, template_name: str, context: dict) -> str:
        """Render *template_name* with the given *context* dict.

        Raises:
            jinja2.TemplateNotFound: If the template does not exist.
            jinja2.TemplateRuntimeError: If a filter references a missing tier.
        """
        template = self._env.get_template(template_name)
        return template.render(context)
