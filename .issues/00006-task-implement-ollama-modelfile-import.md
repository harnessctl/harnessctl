---
id: "00006"
type: task
title: "Implement Ollama Modelfile import"
status: done
parent: "00008"
opencode-agent: lead-engineer
---

# Implement Ollama Modelfile import

## Description

Generate Modelfile and run `ollama create` to import GGUF files into Ollama.

## Tasks

- Create `src/harnessctl/expose/ollama_import.py`
- Function `create_modelfile(model_path: Path, model_name: str) -> Path`:
  - Generate Modelfile content:
    ```
    FROM ./model.gguf
    PARAMETER temperature 0.7
    PARAMETER top_p 0.9
    ```
  - Write to `~/.local/share/harnessctl/models/ollama/<model_name>/Modelfile`
- Function `import_to_ollama(modelfile_path: Path, model_name: str) -> bool`:
  - Run `ollama create <model_name> -f <modelfile_path>` via subprocess
  - Capture stdout/stderr, check exit code
  - Return True on success
- Handle Ollama CLI not installed → warn and skip
- Ensure model path is absolute and accessible

## Acceptance Criteria

- Modelfile generated with correct FROM path
- `ollama create` command executed successfully
- Handles missing Ollama CLI gracefully (warning)
- Unit tests with mocked subprocess
- Works with both relative and absolute paths

## Comments
