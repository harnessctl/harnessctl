---
id: "00007"
type: task
title: "Implement post-pull registration into models.yaml"
status: done
parent: "00008"
opencode-agent: lead-engineer
---

# Implement post-pull registration into models.yaml

## Description

Write a model registration fragment to `models.yaml` after a successful pull to make it available for compilation.

## Tasks

- Create `src/harnessctl/expose/register.py`
- Implement `register_model(model_data: dict, spec_path: Path)`:
  - Load existing `models.yaml` (or create if missing)
  - Append or update the model entry with:
    - `name`: unique identifier
    - `source`: the `hf:` or `ollama:` source string
    - `via`: list of compatible engines (from matrix)
    - `path`: absolute path to the local model file
- Ensure the registration is idempotent (don't create duplicates)
- Handle file locking or atomic writes to prevent corruption
- Integrate with the puller to trigger registration on completion

## Acceptance Criteria

- Models correctly appear in `models.yaml` after pull
- `via` entries match detected engine compatibility
- Absolute paths are correctly resolved and stored
- Existing entries are updated if the same model is re-pulled
- Unit tests verify YAML structure and content

## Comments
