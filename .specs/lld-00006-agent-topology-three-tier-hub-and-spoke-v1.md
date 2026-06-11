---
id: "00006"
type: lld
title: "Agent Topology Three Tier Hub and Spoke"
version: 1
status: draft
parent: "00001"
opencode-agent: lead-engineer
---

# Agent Topology Three Tier Hub and Spoke

## Context

Implements the **3-tier agent design** layered on top of Req 1/2. Both target
harnesses cap agent nesting at 2 levels (orchestrator + leaf subagent — a
subagent cannot spawn another). This LLD models 3 _logical_ tiers as
**model-bound roles mediated by one hub orchestrator** (Solution A,
hub-and-spoke), with an opt-in out-of-process escape hatch (Solution B) for true
depth. Authored as templates per LLD-00002; tiers resolve to models per
LLD-00003.

Agreed topology:

```yaml
tiers:
  reasoning:   { primary: <opus/o3-class> }   # design docs, hard algorithms
  balanced:    { primary: <mid model> }        # LLDs, code comprehension, impl
  cheap_local: { via: ollama|mlx, id: <coder> }# write code from precise spec

agents:
  orchestrator: { tier: balanced,    role: hub,    can_delegate: [thinker, mid, coder] }
  thinker:      { tier: reasoning,   role: worker }
  mid:          { tier: balanced,    role: worker, escalates_to: thinker }
  coder:        { tier: cheap_local, role: worker, escalates_to: mid }
```

## Approach

**Hub-and-spoke (Solution A — default).** The orchestrator is the only
delegator. It is deliberately a _balanced_ (non-reasoning) model whose job is
**routing, sequencing, and verdict aggregation only** — it must never judge
content quality itself. Quality judgment is delegated (e.g. thinker-B validates
thinker-A's output); the orchestrator records the verdict.

**Escalation as return-then-reroute, not call-up.** Workers never call upward
(impossible within the 2-level cap and unnecessary in hub topology). A worker
returns a **structured verdict**; the orchestrator reroutes:

| Verdict                    | Emitted by               | Orchestrator action              |
| -------------------------- | ------------------------ | -------------------------------- |
| `DONE`                     | any worker               | proceed / next step              |
| `APPROVED`                 | thinker/mid (validation) | accept artifact                  |
| `CHANGES{...}`             | thinker/mid              | send back to producer with notes |
| `ESCALATE{reason,context}` | mid                      | dispatch to `thinker`            |
| `NEEDS_SPEC{gap}`          | coder                    | dispatch to `mid` to refine spec |

`escalates_to` in the spec is a **routing hint** the orchestrator consults; the
orchestrator owns the actual re-dispatch. The contract is encoded once in a
shared Jinja partial (`partials/escalation.md.j2`) included into every agent
prompt, so all agents speak the same verdict protocol on both harnesses.

**Mis-routing mitigation:** a cheap hub may occasionally route hard work to
`mid` instead of `thinker`. Accepted tradeoff — `mid` escalates freely, which
self-corrects at the cost of one wasted `mid` round.

**Out-of-process depth (Solution B — opt-in).** For genuine depth >2, an agent
edge marked `delegate_via: cli` invokes the lower agent as a separate harness
process (`opencode run --agent coder "<spec>"` or
`PI_CODING_AGENT_DIR=… pi run ...`). Bypasses the nesting cap via process
isolation; handoff is text-only. Used only where hub routing is insufficient.

**Compilation:** each agent renders to the harness's agent/subagent file with
its `tier`-resolved model. If a harness can't set a per-subagent model
(`supports_subagent_model=false`), the emitter injects the model directive into
the prompt body + `WARN` (reuses LLD-00002 degradation).

## File Changes

| File                                  | Change                                                                              |
| ------------------------------------- | ----------------------------------------------------------------------------------- |
| `templates/partials/escalation.md.j2` | Shared verdict/escalation contract include.                                         |
| `templates/agents/orchestrator.md.j2` | Hub prompt: route-only, no content judgment, aggregation rules.                     |
| `templates/agents/thinker.md.j2`      | Reasoning worker prompt.                                                            |
| `templates/agents/mid.md.j2`          | Balanced worker prompt; escalation to thinker.                                      |
| `templates/agents/coder.md.j2`        | Local coder prompt; `NEEDS_SPEC` behavior.                                          |
| `src/harnessctl/spec/models.py`       | Extend `Agent` with `role`, `tier`, `can_delegate`, `escalates_to`, `delegate_via`. |
| `src/harnessctl/agents/topology.py`   | Validate topology (hub exists, tiers resolve, no illegal in-process depth).         |

## Tasks

1. Extend `Agent` model with role/tier/delegation fields + enum for `delegate_via`. (`spec/models.py`)
2. Implement topology validation: exactly one hub, `can_delegate`/`escalates_to` refer to existing agents, in-process edges respect 2-level cap, `delegate_via: cli` required for deeper edges. (`agents/topology.py`)
3. Author the shared escalation-contract partial. (`templates/partials/escalation.md.j2`)
4. Author the 4 agent prompt templates with tier-aware, capability-gated bodies. (`templates/agents/*.j2`)
5. Wire topology validation into the semantic pass (LLD-00001) and emit (LLD-00002). (`agents/topology.py`)
6. Tests: verdict protocol present in all rendered agents, illegal deep in-process edge rejected, `cli` edge accepted, model-in-prompt fallback when subagent model unsupported. (`tests/agents/`)

## Edge Cases

- **Orchestrator tries to self-judge** — prompt explicitly forbids; validation can't enforce at runtime, so contract + tests on prompt content guard it.
- **Cyclic delegation** (mid→coder→mid loop) — topology validator detects cycles in `can_delegate` graph; allowed only as return-verdicts, not delegation edges.
- **`delegate_via: cli` but target harness binary absent** — runtime concern; document + recommend Solution A default.
- **Tier resolves to a model not installed/available** — surfaced by LLD-00004 discovery at compile-time `--check`; `WARN`.
- **Harness lacks subagent concept entirely** — emit all as top-level agents + `WARN` that escalation is prompt-mediated only.

## Decisions

- **Hub-and-spoke (A)** over forced nesting — respects the real 2-level cap; matches proven pattern; simpler inter-agent language.
- **Orchestrator = balanced, route-only** — cheap coordination; quality delegated to reasoning, preventing a cheap model from making quality calls.
- **Return-then-reroute** over call-up — the only thing physically possible, and cleaner.
- **CLI out-of-process as opt-in escape hatch** — true depth available without complicating the default.
- **Contract in one partial** — single source for the verdict protocol across harnesses.

## Assumptions

- OpenCode subagents and Pi agents each accept a per-agent model; if not, prompt-level fallback applies.
- The user authors task-routing policy in the orchestrator prompt (which tier for which task class).
- Verdict protocol is prompt-enforced (LLM-followed), not runtime-validated — acceptable for a personal toolchain.
