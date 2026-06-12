---
id: "00009"
type: task
title: "Extend Agent model and implement topology validation"
status: open
parent: "00006"
opencode-agent: lead-engineer
---

# Extend Agent model and implement topology validation

## Description

Extend the `Agent` dataclass in `src/harnessctl/spec/models.py` with 3-tier topology fields and implement validation logic in `src/harnessctl/agents/topology.py`.

## Tasks

- [ ] Add fields to `Agent` in `src/harnessctl/spec/models.py`:
  - `role`: str ("hub" or "worker")
  - `tier`: str (references a tier name)
  - `can_delegate`: List[str] (agent names)
  - `escalates_to`: Optional[str] (agent name)
  - `delegate_via`: str ("harness" or "cli", default "harness")
- [ ] Implement `src/harnessctl/agents/topology.py`:
  - `validate_topology(spec: Spec)`:
    - Exactly one hub exists.
    - `can_delegate` and `escalates_to` refer to existing agents.
    - In-process depth (hub -> worker) is max 1 level unless `delegate_via` is "cli".
    - No cycles in the delegation graph.
- [ ] Integrate `validate_topology` into the main semantic validation pass in `src/harnessctl/spec/validate.py`.

## Acceptance Criteria

- `Agent` model supports all required topology fields.
- Topology validation correctly identifies missing hubs or multiple hubs.
- Illegal nesting depth (>1 level without CLI escape) is rejected.
- Cycles are detected and reported.

## Comments
