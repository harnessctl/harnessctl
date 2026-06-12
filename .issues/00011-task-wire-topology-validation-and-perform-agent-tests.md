---
id: "00011"
type: task
title: "Wire topology validation and perform agent tests"
status: open
parent: "00006"
opencode-agent: lead-engineer
---

# Wire topology validation and perform agent tests

## Description

Finalize the integration of the topology validation into the emitters and write comprehensive tests for the agent hierarchy.

## Tasks

- [ ] Update `src/harnessctl/emit/base.py` or emitters to handle `delegate_via: cli` (Solution B).
- [ ] Implement model-in-prompt fallback in `OpenCodeEmitter` and `PiEmitter` when per-subagent model setting is unsupported.
- [ ] Create `tests/agents/test_topology.py`:
  - Test valid hub-and-spoke.
  - Test invalid nesting.
  - Test cycle detection.
- [ ] Create `tests/agents/test_prompts.py`:
  - Verify verdict protocol is rendered in all agents.
  - Verify model fallback directives.

## Acceptance Criteria

- Full agent hierarchy can be compiled and emitted.
- Emitters correctly warn or fallback for unsupported subagent models.
- All topology and prompt tests pass.

## Comments
