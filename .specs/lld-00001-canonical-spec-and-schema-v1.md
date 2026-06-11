---
id: "00001"
type: lld
title: "Canonical Spec and Schema"
version: 1
status: draft
opencode-agent: lead-engineer
---

# Canonical Spec and Schema

## Context

Foundation LLD for `harnessctl` (working name) — a Python tool that compiles one
canonical configuration into native configs for multiple AI coding harnesses
(OpenCode, Pi.dev), propagates MCP + model settings, lists model pricing, and
recommends/pulls local models.

This LLD defines the **Intermediate Representation (IR)**: the single
source-of-truth schema every other subsystem reads from. All sibling LLDs
(00002–00007) depend on the types defined here. No harness config is ever the
source of truth — this IR is.

Cross-LLM consensus driving this design: _own registry = source of truth_,
_capabilities not fields_, _warnings not silent drops_.

## Approach

A layered YAML spec, loaded and validated into **Pydantic v2** models. The spec
is split across multiple files under a config root (default
`~/.config/harnessctl/`, overridable via `HARNESSCTL_HOME` and `--config`),
merged deterministically:

```
~/.config/harnessctl/
  harnessctl.yaml      # top-level: version, defaults, harness targets
  tiers.yaml           # model tiers (reasoning/balanced/cheap_local)
  models.yaml          # logical models -> runtime source mappings
  mcp.yaml             # MCP server definitions
  agents.yaml          # agent topology (see LLD-00006)
  profiles.yaml        # cost/routing profiles
  templates/           # Jinja2 sources (see LLD-00002)
  overrides/           # per-harness raw passthrough blocks
```

**Merge order** (lowest→highest precedence): packaged defaults → user config
root → project-local `.harnessctl/` → CLI flags. Merge is deep-dict for maps,
replace for scalars/lists (lists are replace-not-append to keep behavior
predictable).

**Validation strategy:** one root model `Spec` aggregates sub-models. Pydantic
provides structural validation; a second **semantic validation pass**
(`validate_references`) checks cross-references that types alone can't:
every `agent.tier` exists in `tiers`, every `tier.primary`/`fallback` model
exists in `models`, every `model.via` runtime is known, every
`profile.preferred` resolves. Violations raise `SpecError` with file+path
context.

**Capabilities model:** harness targets are described by a `HarnessCapabilities`
record (e.g. `supports_subagent_model: bool`,
`supports_tool_permissions: "full"|"partial"|"none"`,
`supports_mcp: bool`). Emitters (LLD-00002/00003) consult capabilities to decide
whether a canonical field becomes native config, prompt text, or a `WARN`.

**Scopes model (multi-destination per harness):** a single harness can be
configured at several **destination scopes**, and the compiler must be able to
emit to _all_ supported scopes (or a selected subset). Each `HarnessTarget`
therefore owns an ordered list of `HarnessScope` records:

```yaml
harness:
  opencode:
    capabilities: { ... }
    scopes:
      - { name: global, kind: global, path: "~/.config/opencode" }
      - { name: project, kind: project, path: "{project}/.opencode" }
  pi:
    capabilities: { ... }
    scopes:
      - { name: global, kind: global, path: "~/.pi" }
      - { name: project, kind: project, path: "{project}" }
      - { name: custom, kind: custom, path: "{project}/.custom-pi", launch_env: { PI_CODING_AGENT_DIR: "{path}" } }
```

`HarnessScope` fields: `name` (unique within a harness), `kind`
(`global|project|custom`), `path` (template string; supports `{project}`,
`{home}`, `~`, env expansion), optional `launch_env` (env vars the harness must
be launched with to actually read this scope, e.g. `PI_CODING_AGENT_DIR`,
`COPILOT_HOME`), and `enabled`. The IR carries scopes as data only; path
resolution and emission belong to the emitter (LLD-00002). When `launch_env` is
present, the compiler reports the exact env needed to activate that scope (a
custom dir is inert unless launched with its var set).

**Warning channel:** a shared `WarningCollector` is threaded through load +
emit. Nothing is silently dropped; unmappable settings produce structured
warnings (`harness`, `field`, `reason`, `fallback`) surfaced by the CLI.

## File Changes

| File                              | Change                                                                                                                                            |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pyproject.toml`                  | Project metadata, deps (pydantic, pyyaml, jinja2, typer, rich, httpx, huggingface_hub), uv build backend, `harnessctl` entrypoint.                |
| `src/harnessctl/__init__.py`      | Package init, version.                                                                                                                            |
| `src/harnessctl/spec/models.py`   | Pydantic models: `Spec`, `Tier`, `Model`, `ModelSource`, `MCPServer`, `Agent`, `Profile`, `HarnessTarget`, `HarnessScope`, `HarnessCapabilities`. |
| `src/harnessctl/spec/loader.py`   | File discovery, deterministic deep-merge, YAML parse into `Spec`.                                                                                 |
| `src/harnessctl/spec/validate.py` | `validate_references` semantic pass; `SpecError`.                                                                                                 |
| `src/harnessctl/spec/warnings.py` | `WarningCollector`, `Warning` dataclass.                                                                                                          |
| `src/harnessctl/spec/defaults/*`  | Packaged default YAML shipped with the wheel.                                                                                                     |

## Tasks

1. Scaffold project — `pyproject.toml`, `src/harnessctl/` layout, uv lock. (`pyproject.toml`, `__init__.py`)
2. Define Pydantic models for all IR entities with field docs and enums for runtimes/capabilities. Include `HarnessScope` (name/kind/path/launch_env/enabled) on `HarnessTarget`. (`spec/models.py`)
3. Implement `WarningCollector`. (`spec/warnings.py`)
4. Implement loader: discovery, deep-merge precedence, YAML→`Spec`. (`spec/loader.py`)
5. Implement semantic `validate_references` + `SpecError`. (`spec/validate.py`)
6. Ship packaged default specs + a documented example config. (`spec/defaults/*`)
7. Unit tests: merge precedence, reference validation failures, capability gating. (`tests/spec/`)

## Edge Cases

- **Missing sub-file** — treated as empty map, defaults apply; no error unless a required reference breaks.
- **Duplicate logical model id across files** — higher-precedence file wins; emit a `WARN` noting the shadow.
- **Unknown runtime in `model.via`** — `SpecError` (typo protection), with the closest known runtime suggested.
- **Tier references a model not present** — `SpecError` at validate pass, not at emit time (fail fast).
- **List vs map merge ambiguity** — lists always replace; documented to avoid surprise appends.
- **Duplicate scope `name` within one harness** — `SpecError` (scopes addressed by name on the CLI; must be unique).
- **Custom scope without `launch_env`** — allowed but `WARN`: files emitted there will be inert unless the harness is pointed at the dir some other way.
- **`HARNESSCTL_HOME` unset** — fall back to XDG `~/.config/harnessctl/`.

## Decisions

- **Pydantic v2** over dataclasses/`cerberus` — runtime validation + JSON schema export + clear errors, lowest-effort for nested config.
- **Multi-file split** over one mega-YAML — keeps concerns isolated (ChatGPT "YAML soup" warning) and lets emitters load only what they need.
- **Lists replace, not merge** — predictability over cleverness.
- **Semantic pass separate from Pydantic** — cross-entity references can't be expressed cleanly in field validators alone.
- **Capabilities as data** — emitters stay declarative; adding a harness = adding a capability record + emitter, no core changes.
- **Scopes as a list on the target** — a harness is not one path but N destinations (global/project/custom). Modeling scopes as data lets the compiler fan out to all of them and lets `launch_env` travel with the dir that needs it.

## Assumptions

- Python 3.11+ runtime (matches uv/uvx distribution, LLD-00007).
- Config is hand-authored YAML; a future `harnessctl init` scaffolds it (LLD-00007).
- Single-user local tool; no concurrent writers to the config root in v1.
- Linux-first; macOS fields (MLX) parse everywhere but are capability-gated at use (LLD-00004/00005).
