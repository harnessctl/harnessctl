from dataclasses import dataclass
from typing import Optional

from harnessctl.spec.models import ModelSource, ModelVia
from harnessctl.providers.secrets import format_env_placeholder


@dataclass
class ResolvedConnection:
    base_url: Optional[str]
    model_id: str
    key_ref: Optional[str]
    kind: str


class ProviderResolver:
    """
    Normalizes a ModelSource into a ResolvedConnection specifying the endpoint and credentials.
    """

    @staticmethod
    def resolve(source: ModelSource) -> ResolvedConnection:
        base_url = source.base_url
        key_ref = source.key_ref
        kind = "openai"  # OpenAI-compatible /v1 is the universal substrate

        if source.via == ModelVia.OPENROUTER:
            base_url = base_url or "https://openrouter.ai/api/v1"
            key_ref = key_ref or format_env_placeholder("OPENROUTER_KEY")
        elif source.via == ModelVia.OPENAI:
            base_url = base_url or "https://api.openai.com/v1"
            key_ref = key_ref or format_env_placeholder("OPENAI_API_KEY")
        elif source.via == ModelVia.ANTHROPIC:
            # Anthropic doesn't use OpenAI compat by default for many harnesses,
            # but if it does, base_url is usually not needed or specific.
            # We map kind to "anthropic" to let emitters decide.
            kind = "anthropic"
            key_ref = key_ref or format_env_placeholder("ANTHROPIC_API_KEY")
        elif source.via == ModelVia.ABACUS:
            base_url = base_url or "https://pa.abacus.ai/api/v1"
            key_ref = key_ref or format_env_placeholder("ABACUS_API_KEY")
        elif source.via == ModelVia.OLLAMA:
            base_url = base_url or "http://localhost:11434/v1"
        elif source.via == ModelVia.LMSTUDIO:
            base_url = base_url or "http://localhost:1234/v1"
        elif source.via == ModelVia.LLAMACPP:
            base_url = base_url or "http://localhost:8080/v1"
        elif source.via == ModelVia.MLX:
            # mlx_lm.server default
            base_url = base_url or "http://localhost:8080/v1"

        return ResolvedConnection(
            base_url=base_url,
            model_id=source.id,
            key_ref=key_ref,
            kind=kind,
        )
