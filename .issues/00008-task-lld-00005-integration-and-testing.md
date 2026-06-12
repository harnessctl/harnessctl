---
id: "00008"
type: task
title: "LLD-00005 Integration and Testing"
status: done
parent: "00008"
opencode-agent: lead-engineer
---

# LLD-00005 Integration and Testing

## Description

Perform final integration of LLD-00005 components and execute the comprehensive test suite.

## Tasks

- Implement `tests/recommend/` and `tests/expose/` test suites
- Verify fit math against known model sizes (7B, 13B, 70B)
- Verify GGUF accessibility across llama.cpp, LM Studio, and Ollama
- Verify MLX is correctly gated to macOS
- Perform a round-trip integration test:
  1. Detect system profile
  2. Recommend a small model (e.g., TinyLlama)
  3. Mock download
  4. Register in `models.yaml`
  5. Run `compile` (LLD-00003) to verify propagation to harness configs
- Fix any identified regressions or edge cases

## Acceptance Criteria

- All 8 tasks of LLD-00005 are verified as working
- Test coverage meets project standards
- Integration test successfully propagates a pulled model to harness configs
- No regressions in LLD-00001 through LLD-00004 components

## Comments
