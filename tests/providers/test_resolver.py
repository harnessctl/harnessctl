from harnessctl.spec.models import ModelSource, ModelVia
from harnessctl.providers.resolver import ProviderResolver


def test_resolver_openrouter():
    source = ModelSource(via=ModelVia.OPENROUTER, id="openai/gpt-4o")
    conn = ProviderResolver.resolve(source)
    assert conn.base_url == "https://openrouter.ai/api/v1"
    assert conn.model_id == "openai/gpt-4o"
    assert conn.key_ref == "${env:OPENROUTER_KEY}"
    assert conn.kind == "openai"


def test_resolver_ollama():
    source = ModelSource(via=ModelVia.OLLAMA, id="llama3")
    conn = ProviderResolver.resolve(source)
    assert conn.base_url == "http://localhost:11434/v1"
    assert conn.model_id == "llama3"
    assert conn.key_ref is None
    assert conn.kind == "openai"


def test_resolver_openai():
    source = ModelSource(via=ModelVia.OPENAI, id="gpt-4o")
    conn = ProviderResolver.resolve(source)
    assert conn.base_url == "https://api.openai.com/v1"
    assert conn.model_id == "gpt-4o"
    assert conn.key_ref == "${env:OPENAI_API_KEY}"
    assert conn.kind == "openai"


def test_resolver_anthropic():
    source = ModelSource(via=ModelVia.ANTHROPIC, id="claude-3-5-sonnet")
    conn = ProviderResolver.resolve(source)
    assert conn.base_url is None
    assert conn.model_id == "claude-3-5-sonnet"
    assert conn.key_ref == "${env:ANTHROPIC_API_KEY}"
    assert conn.kind == "anthropic"


def test_resolver_overrides():
    source = ModelSource(
        via=ModelVia.OLLAMA,
        id="qwen2",
        base_url="http://remote-ollama:11434/v1",
        key_ref="${env:CUSTOM_KEY}",
    )
    conn = ProviderResolver.resolve(source)
    assert conn.base_url == "http://remote-ollama:11434/v1"
    assert conn.key_ref == "${env:CUSTOM_KEY}"
