---
id: "00010"
type: task
title: "Implement agent prompt templates and escalation contract"
status: open
parent: "00006"
opencode-agent: lead-engineer
---

# Implement agent prompt templates and escalation contract

## Description

Author the Jinja2 templates for the 3-tier agent roles and the shared escalation verdict protocol.

## Tasks

- [ ] Create `src/harnessctl/spec/defaults/templates/partials/escalation.md.j2`:
  - Define the verdict protocol (`DONE`, `APPROVED`, `CHANGES`, `ESCALATE`, `NEEDS_SPEC`).
- [ ] Create `src/harnessctl/spec/defaults/templates/agents/orchestrator.md.j2`:
  - Hub role: routing, sequencing, no content judgment.
- [ ] Create `src/harnessctl/spec/defaults/templates/agents/thinker.md.j2`:
  - Reasoning worker: deep analysis, design, validation.
- [ ] Create `src/harnessctl/spec/defaults/templates/agents/mid.md.j2`:
  - Balanced worker: implementation, LLDs, escalates to thinker.
- [ ] Create `src/harnessctl/spec/defaults/templates/agents/coder.md.j2`:
  - Local coder: focused implementation from spec, returns `NEEDS_SPEC`.

## Acceptance Criteria

- Escalation partial correctly defines the cross-agent communication protocol.
- Orchestrator template explicitly forbids self-judgment.
- All templates include the escalation partial.
- Templates are located in the correct defaults directory.

## Comments
