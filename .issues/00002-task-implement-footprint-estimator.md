---
id: "00002"
type: task
title: "Implement footprint estimator"
status: done
parent: "00008"
opencode-agent: lead-engineer
---

# Implement footprint estimator

## Description

Implement memory footprint estimation per quantization and fit predicate.

## Tasks

- Create `src/harnessctl/recommend/estimate.py`
- Define quantization mapping: `{"Q4_K_M": 4.5, "Q5_K_M": 5.5, "Q8_0": 8.0}` bits per param
- Implement `estimate_footprint(model_size_b: int, quant: str) -> float`:
  - Convert bits per param to bytes: `bits_per_param / 8`
  - Multiply by model size (params in billions)
  - Apply overhead factor (~1.2)
  - Return GB required
- Implement `fits_in_memory(model_size_b: int, quant: str, profile: SystemProfile) -> bool`:
  - Calculate required GB
  - Compare against `profile.ram_gb` + `profile.vram_gb` (if available)
  - Return True if fits
- Handle unknown quantization: raise ValueError
- Write unit tests with known model sizes (e.g., 7B, 13B, 70B)

## Acceptance Criteria

- Accurate GB estimates for common quantizations
- Overhead factor applied correctly
- Fit predicate works with SystemProfile
- Edge cases: unknown quant, zero size, negative size
- Tests verify calculations against manual examples

## Comments
