---
id: "00003"
type: task
title: "Implement HF candidate search and ranker"
status: done
parent: "00008"
opencode-agent: lead-engineer
---

# Implement HF candidate search and ranker

## Description

Implement HF candidate search filtered by tags (GGUF, coding, instruct) and rank by fit/capability.

## Tasks

- Create `src/harnessctl/recommend/ranker.py`
- Use `huggingface_hub` to list models filtered by tags:
  - `gguf` (format availability)
  - `text-generation-inference`
  - `instruct`
  - `coding`
- Define `RankedModel` dataclass:
  - `repo_id: str`
  - `quant: str`
  - `size_bytes: int`
  - `estimated_memory_gb: float`
  - `backend: str` (llama.cpp, MLX, etc.)
  - `confidence: float`
- Implement ranking algorithm:
  1. Filter candidates with GGUF availability
  2. For each candidate, compute footprint per quantization
  3. Filter by fit (`fits_in_memory`)
  4. Score by capability (larger quant → higher score)
  5. Sort by score descending
- Return ranked shortlist: `List[RankedModel]`
- Write unit tests with mocked HF API responses

## Acceptance Criteria

- Filters models by GGUF tag
- Computes footprint using `estimate_footprint`
- Filters out models that don't fit system memory
- Ranks by quantization size (larger = better capability)
- Returns top 5 candidates
- Handles API errors gracefully

## Comments
