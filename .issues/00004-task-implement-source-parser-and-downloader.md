---
id: "00004"
type: task
title: "Implement source parser and downloader"
status: done
parent: "00008"
opencode-agent: lead-engineer
---

# Implement source parser and downloader

## Description

Implement source prefix parsing (`hf:`, `ollama:`, URL) and HF downloader into shared store.

## Tasks

- Create `src/harnessctl/pull/sources.py`:
  - Parse source prefixes: `hf:<repo>[:<file>]`, `ollama:<name>`, direct GGUF URL
  - Return structured `Source` object
- Create `src/harnessctl/pull/huggingface.py`:
  - `HuggingFaceDownloader` class
  - Use `hf_hub_download` or `snapshot_download`
  - Target directory: `~/.local/share/harnessctl/models/huggingface/<repo>/`
  - Resume support via HF hub
  - Pre-check disk space before download
- Create `src/harnessctl/pull/ollama.py`:
  - Wrapper for `ollama pull <name>` via subprocess
  - Map to local store path
- Shared model store structure:
  ```
  ~/.local/share/harnessctl/models/
    ├── huggingface/
    │   └── <repo>/<file>.gguf
    ├── ollama/
    │   └── <name>/...
    └── urls/
        └── <hash>.gguf
  ```
- Handle errors: network failures, insufficient disk space, invalid URLs

## Acceptance Criteria

- Source parser correctly identifies HF, Ollama, and URL sources
- HF downloader downloads GGUF files to correct location
- Ollama wrapper calls `ollama pull` and tracks location
- Disk space pre-check prevents OOM downloads
- Resume works for interrupted downloads
- Unit tests with mocked HF API and subprocess

## Comments
