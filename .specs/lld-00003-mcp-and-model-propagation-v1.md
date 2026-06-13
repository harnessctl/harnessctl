---
id: "00003"
type: lld
title: "MCP and Model Propagation"
version: 1
status: deprecated
parent: "00001"
opencode-agent: lead-engineer
---

# MCP and Model Propagation

## Context

Implements **Req 2**: propagate identical MCP server definitions and LLM model
settings across all harnesses — especially proxied providers (OpenRouter,
Abacus) and local runtimes (Ollama, MLX, llama.cpp, LM Studio). Consumes the IR
(LLD-00001) and shares the emit infrastructure (LLD-00002). This LLD owns the
_settings_ artifacts (JSON/JSONC config), 00002 owns _content_ artifacts.

## Approach

**Canonical declarations** (from `models.yaml`, `mcp.yaml`):

```yaml
mcp:
  servers:
    - id: github
      transport: stdio # stdio | http | sse
      command: ["gh-mcp"] # for stdio
      url: null # for http/sse
      env: { GITHUB_TOKEN: "${env:GH_TOKEN}" }

models:
  gpt-x: { via: openrouter, id: openai/gpt-4o, cost_ref: openai/gpt-4o }
  claude-r: { via: anthropic, id: claude-3-7-sonnet }
  qwen: { via: ollama, id: qwen2.5-coder:7b, endpoint: http://localhost:11434 }
  qwen-mlx: { via: mlx, id: mlx-community/Qwen2.5-Coder-7B-4bit }
```

**Provider normalization:** a `ProviderResolver` turns each `model.via` into the
concrete connection a harness needs: `base_url`, `api_key_ref`, `provider_kind`
(openai-compatible vs native). Key insight — **proxied + local runtimes all speak
OpenAI-compatible `/v1`**, so for most harnesses one logical model becomes one
`{base_url, model_id, api_key}` triple, identical everywhere. Native providers
(anthropic) map to the harness's native provider block when supported, else fall
back to their OpenAI-compatible endpoint.

| `via`      | base_url                                   | key source              |
| ---------- | ------------------------------------------ | ----------------------- |
| openrouter | `https://openrouter.ai/api/v1`             | `${env:OPENROUTER_KEY}` |
| abacus     | configured proxy base_url                  | `${env:ABACUS_KEY}`     |
| ollama     | `http://localhost:11434/v1`                | none (`ollama`)         |
| lmstudio   | `http://localhost:1234/v1`                 | none                    |
| llamacpp   | `http://localhost:8080/v1`                 | none                    |
| mlx        | `http://localhost:8080/v1` (mlx_lm.server) | none                    |

**Secret handling:** never inline secrets. The spec uses `${env:VAR}`
placeholders; emitters either pass the placeholder through (if the harness
supports env interpolation) or write a reference and emit a `WARN` instructing
the user to set the env var. Secrets never land in generated files.

**Emitters (extend LLD-00002 `Emitter`):** add `emit_settings()` producing each
harness's settings file:

| Harness  | MCP target                                        | Model/provider target     |
| -------- | ------------------------------------------------- | ------------------------- |
| OpenCode | `opencode.json` `mcp` + `provider`/`model` blocks | same file, `provider` map |
| Pi.dev   | `~/.pi/agent/settings.json` mcp + model           | same file                 |

Capability-gated: if a harness lacks MCP support (`supports_mcp=false`), skip +
`WARN`. If a harness can't express a transport (e.g. only stdio, no http), `WARN`
with the unsupported server named.

## File Changes

| File                                   | Change                                                                      |
| -------------------------------------- | --------------------------------------------------------------------------- |
| `src/harnessctl/providers/resolver.py` | `ProviderResolver`: `via` → `{base_url, model_id, key_ref, kind}`.          |
| `src/harnessctl/providers/secrets.py`  | `${env:VAR}` placeholder parsing + passthrough policy.                      |
| `src/harnessctl/emit/opencode.py`      | Add `emit_settings`: write `mcp` + `provider`/`model` into `opencode.json`. |
| `src/harnessctl/emit/pi.py`            | Add `emit_settings`: write mcp + model into `~/.pi/agent/settings.json`.    |
| `src/harnessctl/emit/jsonmerge.py`     | JSON/JSONC structural merge preserving non-managed user keys.               |

## Tasks

1. Implement `ProviderResolver` with the via→connection table + native/OpenAI-compat decision. (`providers/resolver.py`)
2. Implement `${env:VAR}` secret placeholder handling + passthrough policy. (`providers/secrets.py`)
3. Implement JSON/JSONC merge that updates only harnessctl-managed keys, preserving user keys. (`emit/jsonmerge.py`)
4. Extend OpenCode emitter with `emit_settings` (mcp + provider/model). (`emit/opencode.py`)
5. Extend Pi.dev emitter with `emit_settings`. (`emit/pi.py`)
6. Tests: identical model triple across harnesses, secret never inlined, MCP transport gating, user-key preservation on re-emit. (`tests/providers/`, `tests/emit/`)

## Edge Cases

- **Proxied model id format differs per harness** — canonical `id` is the provider's native id; resolver adapts prefix where a harness requires `provider/model`.
- **Local endpoint not running at emit time** — still emit config (config is static); discovery/health is LLD-00004's concern, not a blocker here.
- **Harness stores MCP in a separate file vs inline** — path map per emitter; merge preserves unrelated keys.
- **Two models map to same endpoint+id** — allowed; dedupe only the connection, keep both aliases.
- **Missing env var referenced by `${env:}`** — emit + `WARN`; never fail the whole compile for a secret the user may set later.

## Decisions

- **OpenAI-compatible `/v1` as the universal substrate** — proxied + all 4 local runtimes expose it, collapsing N providers into one connection shape.
- **Env placeholders over inlined keys** — security; generated files are safe to commit/share.
- **Structural JSON merge** over full-file overwrite — preserves user-managed keys the tool doesn't own.
- **Static config emit independent of runtime health** — separation of concerns; compile must work offline.

## Assumptions

- OpenCode `opencode.json` supports a `provider`/`model` map and an `mcp` block; Pi exposes model + mcp in `settings.json`. Exact key names verified at implementation; resolver output is shaped to match.
- Abacus is reachable via an OpenAI-compatible proxy base_url the user configures.
