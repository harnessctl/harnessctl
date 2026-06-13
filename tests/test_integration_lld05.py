import yaml
from unittest.mock import patch, Mock
from harnessctl.sysprobe.profile import detect_system
from harnessctl.recommend.ranker import search_candidates
from harnessctl.recommend.intent import analyze_intent
from harnessctl.pull.sources import parse_source
from harnessctl.pull.huggingface import HuggingFaceDownloader
from harnessctl.expose.matrix import resolve_best_format
from harnessctl.expose.register import register_model


def test_integration_recommend_pull_register(tmp_path):
    # 1. Detect system profile (mocked)
    with (
        patch("psutil.virtual_memory") as mock_mem,
        patch("psutil.cpu_count", return_value=8),
        patch("platform.system", return_value="Linux"),
        patch("platform.machine", return_value="x86_64"),
    ):
        mock_mem.return_value.total = 16 * (1024**3)
        mock_mem.return_value.available = 12 * (1024**3)
        profile = detect_system()

    # 2. Search for candidates (mocked)
    mock_model = Mock()
    mock_model.modelId = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
    mock_files = ["tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"]

    with (
        patch("huggingface_hub.HfApi.list_models", return_value=[mock_model]),
        patch("huggingface_hub.HfApi.list_repo_files", return_value=mock_files),
    ):
        intent = analyze_intent("Recommend a small model")
        candidates = search_candidates(profile, intent, limit=1)
        assert len(candidates) > 0
        best_candidate = candidates[0]

    # 3. Simulate pull
    source_str = f"hf:{best_candidate.id}:{mock_files[0]}"
    source = parse_source(source_str)

    downloader = HuggingFaceDownloader(cache_dir=tmp_path)
    mock_download_path = tmp_path / "huggingface" / best_candidate.id / mock_files[0]
    mock_download_path.parent.mkdir(parents=True, exist_ok=True)
    mock_download_path.touch()

    with patch(
        "harnessctl.pull.huggingface.hf_hub_download",
        return_value=str(mock_download_path),
    ):
        actual_path = downloader.download(source.repo, source.file)
        assert actual_path == mock_download_path

    # 4. Resolve compatibility
    fmt, engines = resolve_best_format(["gguf"], profile)
    assert fmt == "gguf"
    assert "llama.cpp" in engines

    # 5. Register model
    spec_path = tmp_path / "models.yaml"
    register_model(
        model_name="tinyllama",
        source=source_str,
        via=engines,
        path=actual_path,
        spec_path=spec_path,
    )

    # 6. Verify registration
    assert spec_path.exists()
    with open(spec_path, "r") as f:
        data = yaml.safe_load(f)
        assert data["models"][0]["name"] == "tinyllama"
        assert "llama.cpp" in data["models"][0]["via"]
        assert data["models"][0]["path"] == str(actual_path.absolute())
