from harnessctl.spec.models import (
    Spec,
    HarnessTarget,
    HarnessCapabilities,
    HarnessScope,
    ScopeKind,
    Model,
    ModelSource,
    ModelVia,
    MCPServer,
)
from harnessctl.emit.pi import PiEmitter
from harnessctl.spec.warnings import WarningCollector
import json


def test_pi_emit_settings(tmp_path):
    spec = Spec(
        harness={
            "pi": HarnessTarget(
                capabilities=HarnessCapabilities(supports_mcp=True),
                scopes=[
                    HarnessScope(name="test", kind=ScopeKind.GLOBAL, path=str(tmp_path))
                ],
            )
        },
        models={
            "test_model": Model(sources=[ModelSource(via=ModelVia.OLLAMA, id="llama3")])
        },
        mcp={"test_server": MCPServer(command="npx", args=["test"], env={})},
    )

    emitter = PiEmitter()
    warnings = WarningCollector()
    emitter.emit_settings(spec, str(tmp_path), "write", warnings)

    settings_path = tmp_path / "settings.json"
    assert settings_path.exists()

    data = json.loads(settings_path.read_text())
    assert "mcpServers" in data
    assert data["mcpServers"]["test_server"]["command"] == "npx"

    assert "models" in data
    assert "test_model" in data["models"]
    assert data["models"]["test_model"]["provider"] == "openai"
    assert data["models"]["test_model"]["baseUrl"] == "http://localhost:11434/v1"
    assert data["models"]["test_model"]["modelId"] == "llama3"
    assert "apiKey" not in data["models"]["test_model"]
