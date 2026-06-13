from unittest.mock import Mock, patch
from harnessctl.recommend.ranker import search_candidates, RankedModel
from harnessctl.recommend.intent import analyze_intent
from harnessctl.sysprobe.profile import SystemProfile


def test_search_candidates():
    intent = analyze_intent("Write a python script to list files")
    profile = SystemProfile(
        ram_gb=16.0,
        free_ram_gb=8.0,
        cpu_cores=8,
        vram_gb=4.0,
        gpu_kind="nvidia",
        os="linux",
        arch="x86_64",
    )

    mock_model = Mock()
    mock_model.modelId = "TheBloke/CodeLlama-7B-GGUF"

    mock_files = ["codellama-7b.Q4_K_M.gguf", "codellama-7b.F16.gguf", "README.md"]

    with (
        patch("huggingface_hub.HfApi.list_models", return_value=[mock_model]),
        patch("huggingface_hub.HfApi.list_repo_files", return_value=mock_files),
    ):
        candidates = search_candidates(profile, intent, limit=5)
        assert len(candidates) == 1
        assert isinstance(candidates[0], RankedModel)
        assert candidates[0].id == "TheBloke/CodeLlama-7B-GGUF"
        assert candidates[0].quant == "Q4_K_M"
        assert candidates[0].params_billion == 7.0
        assert candidates[0].estimated_memory_gb > 0


def test_search_candidates_empty_repo():
    intent = analyze_intent("Just a simple task")
    profile = SystemProfile(
        ram_gb=16.0,
        free_ram_gb=8.0,
        cpu_cores=8,
        vram_gb=None,
        gpu_kind=None,
        os="linux",
        arch="x86_64",
    )

    mock_model = Mock()
    mock_model.modelId = "empty-repo"

    with (
        patch("huggingface_hub.HfApi.list_models", return_value=[mock_model]),
        patch("huggingface_hub.HfApi.list_repo_files", return_value=[]),
    ):
        candidates = search_candidates(profile, intent, limit=5)
        assert len(candidates) == 0
