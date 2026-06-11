---
id: "00004"
type: lld
title: "Local Discovery and Pricing"
version: 1
status: draft
parent: "00001"
opencode-agent: lead-engineer
---

# Local Discovery and Pricing

## Context

Implements **Req 4** (list prices for online paid models, as accurate as
possible) plus the **local discovery** capability feeding it (what runtimes/models
are alive locally, priced at $0). Consumes IR (LLD-00001). Feeds the model
recommender (LLD-00005) and CLI tables (LLD-00007). v1 is **fetch-on-demand CLI**;
no daemon (deferred to Phase 2).

## Approach

**Discovery engine:** probe each known local runtime over its OpenAI-compatible
(or native) listing endpoint, with short timeouts and graceful skip-if-down:

| Runtime   | Probe                                                 | Parse                                    |
| --------- | ----------------------------------------------------- | ---------------------------------------- |
| Ollama    | `GET :11434/api/tags`                                 | `.models[].name`                         |
| LM Studio | `GET :1234/v1/models`                                 | `.data[].id`                             |
| llama.cpp | `GET :8080/v1/models`                                 | `.data[].id` (usually loaded model only) |
| MLX       | `GET :8080/v1/models` (mlx_lm.server) + HF cache scan | `.data[].id` / dirs                      |

Endpoints come from the spec (overridable). Results normalize into
`DiscoveredModel{runtime, id, endpoint, local=True}`. Discovery is concurrent
(`httpx.AsyncClient` / thread pool) and never fails the command if a service is
offline — it just omits it.

**Pricing source:** pull the **litellm** registry
`model_prices_and_context_window.json` (broad coverage, hundreds of models) as
the primary catalog, plus **OpenRouter** live `/api/v1/models` for proxied
accuracy. Both cached to `~/.cache/harnessctl/pricing/` with a TTL (default 24h,
`--refresh` to force). On fetch failure, fall back to the last cached copy and
`WARN` (never hard-fail a list command). Local discovered models are injected
with `input=output=0.0`.

**Unified catalog:** a `PricedModel{id, provider, input_per_mtok,
output_per_mtok, context_window, local, status}` where `status ∈ {running,
installed, available}` — `running`/`installed` derived from discovery,
`available` from the pricing catalog. The CLI (LLD-00007) renders/sorts this with
Rich; sort keys: `input`, `output`, `context`, `provider`.

**Accuracy stance:** prices are "as accurate as possible" — litellm is
community-maintained and can lag; OpenRouter is authoritative for proxied. We
record `source` + `fetched_at` per row so staleness is visible.

## File Changes

| File                                        | Change                                                    |
| ------------------------------------------- | --------------------------------------------------------- |
| `src/harnessctl/discovery/base.py`          | `RuntimeProbe` ABC, `DiscoveredModel`, concurrent runner. |
| `src/harnessctl/discovery/ollama.py`        | Ollama `/api/tags` probe.                                 |
| `src/harnessctl/discovery/openai_compat.py` | Shared `/v1/models` probe for LM Studio/llama.cpp/MLX.    |
| `src/harnessctl/discovery/mlx.py`           | MLX server probe + HF cache scan (macOS-gated).           |
| `src/harnessctl/pricing/litellm.py`         | Fetch + cache litellm price JSON.                         |
| `src/harnessctl/pricing/openrouter.py`      | Fetch + cache OpenRouter live pricing.                    |
| `src/harnessctl/pricing/catalog.py`         | Merge pricing + discovery → `PricedModel` list; sorting.  |
| `src/harnessctl/pricing/cache.py`           | TTL cache read/write + stale fallback.                    |

## Tasks

1. Implement `RuntimeProbe` ABC + concurrent runner with per-probe timeout and skip-on-error. (`discovery/base.py`)
2. Implement Ollama and shared OpenAI-compat probes. (`discovery/ollama.py`, `discovery/openai_compat.py`)
3. Implement MLX probe + HF cache scan, macOS-gated. (`discovery/mlx.py`)
4. Implement TTL cache with stale fallback + `WARN`. (`pricing/cache.py`)
5. Implement litellm + OpenRouter fetchers. (`pricing/litellm.py`, `pricing/openrouter.py`)
6. Implement catalog merge (`PricedModel`, status derivation, sort keys), local=$0 injection. (`pricing/catalog.py`)
7. Tests: offline service skipped, cache stale-fallback path, local-$0 injection, sort correctness, source/fetched_at recorded. (`tests/discovery/`, `tests/pricing/`)

## Edge Cases

- **All local services down** — catalog still returns priced cloud models; discovery contributes nothing, no error.
- **Pricing fetch fails + no cache** — return cloud rows as empty with a `WARN`; local rows still listed.
- **Model in discovery not in pricing catalog** — listed as local/$0 or `available` with `unknown` price flagged.
- **llama.cpp lists only the loaded model** — accepted; documented limitation.
- **MLX on Linux** — probe disabled by capability gate; no spurious errors.
- **Clock skew / TTL** — `fetched_at` stored as UTC; `--refresh` bypasses TTL.

## Decisions

- **litellm JSON as primary catalog** — broadest free, community-maintained coverage (Gemini/DeepSeek consensus); no key needed.
- **OpenRouter live as proxied overlay** — authoritative for the proxy the user actually bills against.
- **Fetch-on-demand, no daemon (v1)** — matches CLI-only v1 scope; live budget alarms are Phase 2.
- **Never hard-fail list on network error** — stale-with-warning beats unusable.
- **Local = $0 with explicit flag** — honest; energy amortization deferred.

## Assumptions

- Network access available for first fetch; thereafter cache suffices offline.
- Default ports are standard; non-standard ports come from spec endpoints.
- Phase-2 daemon will reuse this discovery + pricing layer unchanged for live alarms.
