---
id: "00001"
type: task
title: "Implement SystemProfile probe"
status: done
parent: "00008"
opencode-agent: lead-engineer
---

# Implement SystemProfile probe

## Description

Create `SystemProfile` dataclass and detection logic for RAM, CPU, GPU/VRAM.

## Tasks

- Create `src/harnessctl/sysprobe/profile.py`
- Define `SystemProfile` dataclass with fields:
  - `ram_gb: float` (total RAM)
  - `vram_gb: Optional[float]` (GPU VRAM if available)
  - `gpu_kind: Optional[str]` (NVIDIA, Apple Metal, etc.)
  - `os: str` (platform.system())
  - `arch: str` (platform.machine())
- Implement detection:
  - RAM via `psutil.virtual_memory()`
  - CPU cores via `psutil.cpu_count()`
  - NVIDIA VRAM via `pynvml` (optional)
  - Apple Metal via `system_profiler` (macOS only)
- OS-gated: MLX detection only on macOS
- Fallback: if VRAM detection fails, set `vram_gb = None`
- Write unit tests mocking different system profiles

## Acceptance Criteria

- `SystemProfile` can be instantiated with detected values
- VRAM detection works on NVIDIA systems (if `pynvml` installed)
- Metal detection works on macOS
- Graceful fallback when GPU detection unavailable
- Tests cover Linux, macOS, and Windows scenarios

## Dependencies

- `psutil` (already in pyproject.toml)
- `pynvml` (optional dependency)

## Comments
