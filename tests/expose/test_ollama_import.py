from pathlib import Path
from unittest.mock import patch
from harnessctl.expose.ollama_import import create_modelfile, import_to_ollama


def test_create_modelfile(tmp_path):
    model_path = tmp_path / "model.gguf"
    model_path.touch()

    modelfile_path = create_modelfile(model_path, "test-model", cache_dir=tmp_path)

    assert modelfile_path.exists()
    assert modelfile_path.name == "Modelfile"

    with open(modelfile_path, "r") as f:
        content = f.read()
        assert f"FROM {model_path.absolute()}" in content


def test_import_to_ollama():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        success = import_to_ollama(Path("/tmp/Modelfile"), "test-model")
        assert success is True
        mock_run.assert_called_once()
        assert "ollama" in mock_run.call_args[0][0]
        assert "create" in mock_run.call_args[0][0]


def test_import_to_ollama_fail():
    with patch("subprocess.run", side_effect=FileNotFoundError):
        success = import_to_ollama(Path("/tmp/Modelfile"), "test-model")
        assert success is False

    with patch("subprocess.run") as mock_run:
        from subprocess import CalledProcessError

        mock_run.side_effect = CalledProcessError(1, "ollama")
        success = import_to_ollama(Path("/tmp/Modelfile"), "test-model")
        assert success is False
