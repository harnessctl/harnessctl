---
id: "00008"
type: lld
title: "Model Recommender Puller and Multi-Engine Exposure"
version: 1
status: draft
parent: "00001"
opencode-agent: lead-engineer
---

# Model Recommender Puller and Multi-Engine Exposure

## Context

Implements **Req 5**: recommend models based on system capabilities, download
them (HuggingFace + other sources), and make them available to as many local
engines as possible. Consumes IR (LLD-00001), discovery (LLD-00004), and feeds
provider config (LLD-00003). Resolves the "one download ≠ usable everywhere"
problem via a **format→compatible-engines** mapping with **GGUF as the common
denominator** (per agreed decision 3).

## Approach

**System probe:** detect host capability budget — total/free RAM, CPU cores, and
GPU/VRAM (NVIDIA via `nvidia-smi`/`pynvml`; Apple Metal via `system_profiler`,
macOS-gated). Produces `SystemProfile{ram_gb, vram_gb, gpu_kind, os, arch}`.

**Recommender:** given a task class and the `SystemProfile`, estimate whether a
candidate model fits. Memory estimate ≈ `params_billion × bytes_per_param(quant) ×
overhead(~1.2)`. Rank HF candidates (filtered by tags like `coding`, instruct,
GGUF availability) by fit-then-capability. Surface a ranked shortlist with
predicted backend + est. footprint; the tool **recommends**, the user confirms
the pull (no silent multi-GB downloads).

**Format → engine compatibility matrix** (the crux of "available to all engines"):

| Format            | llama.cpp | LM Studio | Ollama                | MLX        |
| ----------------- | --------- | --------- | --------------------- | ---------- |
| GGUF              | ✅        | ✅        | ✅ (Modelfile import) | ❌         |
| MLX (safetensors) | ❌        | ❌        | ❌                    | ✅ (macOS) |
| HF safetensors    | (convert) | (convert) | (convert)             | (convert)  |

**Strategy:** prefer pulling a **GGUF** repo/quant → instantly usable by
llama.cpp + LM Studio; for Ollama, generate a `Modelfile` (`FROM ./model.gguf`)
and `ollama create` to import the same file (no re-download). On macOS, if MLX is
targeted, additionally pull the MLX-community variant (separate weights — honestly
flagged as a second download). True universality isn't possible across formats;
we maximize reach from one GGUF artifact and are explicit about the MLX exception.

**Puller:** `huggingface_hub.hf_hub_download` / `snapshot_download` into a
**shared model store** `~/.local/share/harnessctl/models/` (XDG data). Engines
are pointed at this store rather than copying: llama.cpp/LM Studio via path
config, Ollama via Modelfile import referencing the file, MLX via its own cache
symlink. Pull supports source prefixes: `hf:<repo>[:<file>]`,
`ollama:<name>` (wrap `ollama pull`), and direct GGUF URLs.

**Registration:** after pull, write the new model into `models.yaml` (or a
generated fragment) with the right `via` entries so LLD-00003 propagates it to
harnesses on next `compile`. Closing the loop: pull → register → compile → all
harnesses see it.

## File Changes

| File                                     | Change                                                    |
| ---------------------------------------- | --------------------------------------------------------- |
| `src/harnessctl/sysprobe/profile.py`     | RAM/CPU/GPU/VRAM detection → `SystemProfile` (OS-gated).  |
| `src/harnessctl/recommend/estimate.py`   | Footprint estimate per quant; fit check.                  |
| `src/harnessctl/recommend/ranker.py`     | HF candidate search + fit/capability ranking.             |
| `src/harnessctl/pull/huggingface.py`    | HF download into shared store; quant/file selection.      |
| `src/harnessctl/pull/sources.py`        | Source prefix parsing (`hf:`/`ollama:`/url); ollama wrap. |
| `src/harnessctl/expose/matrix.py`       | Format→engine matrix; capability resolution.              |
| `src/harnessctl/expose/ollama_import.py`| Generate Modelfile + `ollama create` from a GGUF.         |
| `src/harnessctl/expose/register.py`     | Write pulled model into `models.yaml` fragment.           |

## Tasks

1. Implement `SystemProfile` probe (RAM/CPU; NVIDIA VRAM; macOS Metal gated). (`sysprobe/profile.py`)
2. Implement footprint estimator + fit predicate per quant. (`recommend/estimate.py`)
3. Implement HF candidate search + ranker (fit-then-capability, GGUF-availability filter). (`recommend/ranker.py`)
4. Implement source parsing + HF downloader into shared store; ollama-pull wrap. (`pull/sources.py`, `pull/huggingface.py`)
5. Implement format→engine matrix. (`expose/matrix.py`)
6. Implement Ollama Modelfile import from GGUF. (`expose/ollama_import.py`)
7. Implement post-pull registration into `models.yaml`. (`expose/register.py`)
8. Tests: fit math vs known sizes, GGUF reaches llama.cpp+LMStudio+Ollama, MLX gated to macOS, registration round-trips into compile. (`tests/recommend/`, `tests/expose/`)

## Edge Cases

- **VRAM detection unavailable** — fall back to RAM-only estimate + `WARN`; recommend conservative quants.
- **Model has no GGUF** — recommend conversion path or skip with explanation; do not silently pull unusable safetensors.
- **Insufficient memory for all quants** — recommend smaller param model or smaller quant; never recommend an OOM config.
- **Ollama not installed** — skip Modelfile import step, still expose to llama.cpp/LM Studio; `WARN`.
- **Disk space low for shared store** — pre-check free space vs estimated download; abort with clear error before downloading.
- **Interrupted download** — rely on HF hub resumable downloads; re-run resumes.
- **MLX requested on Linux** — refuse with clear message (capability gate).

## Decisions

- **GGUF as common denominator** — single artifact serves llama.cpp + LM Studio + Ollama (via import); maximizes reach (agreed decision 3).
- **Shared model store + pointers** over per-engine copies — saves disk; one file, many engines.
- **Recommend-then-confirm** over auto-pull — multi-GB downloads must be explicit.
- **MLX treated as honest exception** — separate weights on macOS; we don't pretend cross-format universality.
- **Register into spec, not directly into harness configs** — keeps IR as source of truth; exposure flows through `compile` (LLD-00003).

## Assumptions

- `huggingface_hub` available; HF auth via standard env/token when needed for gated repos.
- Ollama CLI present when Ollama import is requested.
- macOS + Apple Silicon assumed for any MLX path; Linux focuses on GGUF.
- Quant naming follows common GGUF conventions (Q4_K_M etc.) for estimate heuristics.

