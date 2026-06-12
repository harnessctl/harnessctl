---
id: "00005"
type: task
title: "Implement format→engine compatibility matrix"
status: done
parent: "00008"
opencode-agent: lead-engineer
---

# Implement format→engine compatibility matrix

## Description

Implement format→engine compatibility matrix and capability resolution.

## Tasks

- Create `src/harnessctl/expose/matrix.py`
- Define compatibility mapping:
  ```
  GGUF → ["llama.cpp", "lmstudio", "ollama"]
  MLX (safetensors) → ["mlx"] (macOS only)
  HF safetensors → [] (requires conversion)
  ```
- Implement `get_compatible_engines(format: str, profile: SystemProfile) -> List[str]`:
  - Check OS gate for MLX (macOS only)
  - Return list of compatible engines
- Implement `resolve_best_format(model_repo: str, profile: SystemProfile) -> Tuple[str, List[str]]`:
  - Query HF for available formats (GGUF, safetensors, MLX)
  - Pick best format based on compatibility matrix
  - Return format and list of compatible engines
- Handle edge cases:
  - No GGUF available → return empty list with warning
  - MLX requested on Linux → refuse with clear message
  - Multiple formats available → prefer GGUF

## Acceptance Criteria

- Correct mapping per spec table
- OS gating works (MLX only on macOS)
- `resolve_best_format` returns GGUF when available
- Returns empty list for unsupported formats
- Unit tests for Linux/macOS scenarios

## Comments
