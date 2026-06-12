import yaml
from harnessctl.expose.register import register_model


def test_register_model_new(tmp_path):
    spec_path = tmp_path / "models.yaml"
    model_path = tmp_path / "model.gguf"

    register_model(
        model_name="test-model",
        source="hf:repo/file",
        via=["llama.cpp"],
        path=model_path,
        spec_path=spec_path,
    )

    assert spec_path.exists()
    with open(spec_path, "r") as f:
        data = yaml.safe_load(f)
        assert len(data["models"]) == 1
        assert data["models"][0]["name"] == "test-model"
        assert data["models"][0]["path"] == str(model_path.absolute())


def test_register_model_update(tmp_path):
    spec_path = tmp_path / "models.yaml"
    model_path = tmp_path / "model.gguf"

    # First registration
    register_model(
        model_name="test-model",
        source="hf:repo/file",
        via=["llama.cpp"],
        path=model_path,
        spec_path=spec_path,
    )

    # Update registration
    new_path = tmp_path / "new_model.gguf"
    register_model(
        model_name="test-model",
        source="hf:repo/file",
        via=["llama.cpp", "ollama"],
        path=new_path,
        spec_path=spec_path,
    )

    with open(spec_path, "r") as f:
        data = yaml.safe_load(f)
        assert len(data["models"]) == 1
        assert "ollama" in data["models"][0]["via"]
        assert data["models"][0]["path"] == str(new_path.absolute())
