from unittest.mock import patch
from harnessctl.pull.sources import parse_source
from harnessctl.pull.huggingface import HuggingFaceDownloader


def test_parse_source_hf():
    s = parse_source("hf:TheBloke/CodeLlama-7B-GGUF:codellama-7b.Q4_K_M.gguf")
    assert s.type == "hf"
    assert s.repo == "TheBloke/CodeLlama-7B-GGUF"
    assert s.file == "codellama-7b.Q4_K_M.gguf"


def test_parse_source_ollama():
    s = parse_source("ollama:llama3")
    assert s.type == "ollama"
    assert s.repo == "llama3"


def test_parse_source_url():
    s = parse_source("https://example.com/model.gguf")
    assert s.type == "url"
    assert s.url == "https://example.com/model.gguf"


def test_hf_downloader(tmp_path):
    downloader = HuggingFaceDownloader(cache_dir=tmp_path)
    assert downloader.cache_dir == tmp_path / "huggingface"

    with patch(
        "harnessctl.pull.huggingface.hf_hub_download",
        return_value=str(tmp_path / "file.gguf"),
    ):
        path = downloader.download("repo", "file.gguf")
        assert path == tmp_path / "file.gguf"
