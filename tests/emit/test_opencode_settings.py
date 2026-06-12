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
from harnessctl.emit.opencode import OpenCodeEmitter
from harnessctl.spec.warnings import WarningCollector
import json


def test_opencode_emit_settings(tmp_path):
    spec = Spec(
        harness={
            "opencode": HarnessTarget(
                capabilities=HarnessCapabilities(supports_mcp=True),
                scopes=[
                    HarnessScope(name="test", kind=ScopeKind.GLOBAL, path=str(tmp_path))
                ],
            )
        },
        models={
            "test_model": Model(
                sources=[ModelSource(via=ModelVia.OPENROUTER, id="test/id")]
            )
        },
        mcp={
            "test_server": MCPServer(
                command="npx", args=["-y", "some-server"], env={"FOO": "bar"}
            )
        },
    )

    emitter = OpenCodeEmitter()
    warnings = WarningCollector()
    emitter.emit_settings(spec, str(tmp_path), "write", warnings)

    settings_path = tmp_path / "opencode.json"
    assert settings_path.exists()

    data = json.loads(settings_path.read_text())
    assert "mcp" in data
    assert data["mcp"]["servers"]["test_server"]["command"] == "npx"
    assert data["mcp"]["servers"]["test_server"]["args"] == ["-y", "some-server"]

    assert "provider" in data
    assert "provider_openai" in data["provider"]
    assert data["provider"]["provider_openai"]["type"] == "openai"
    assert data["provider"]["provider_openai"]["url"] == "https://openrouter.ai/api/v1"

    assert "model" in data
    assert "test_model" in data["model"]
    assert data["model"]["test_model"]["provider"] == "provider_openai"
    assert data["model"]["test_model"]["id"] == "test/id"
