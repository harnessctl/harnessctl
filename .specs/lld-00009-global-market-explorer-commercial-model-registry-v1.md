---
id: "00009"
status: done
type: lld
title: "Global Market Explorer (Commercial Model Registry)"
version: 1

opencode-agent: lead-engineer
---

# LLD-00009: Global Market Explorer (Commercial Model Registry)

This LLD defines a standalone script and CLI command to explore the global commercial LLM market, addressing the user's need for a "proper" way to list, filter, and sort all existing models by price, intelligence, and speed.

## 1. Data Sources

- **OpenRouter API**: Primary source for long-tail models and unified pricing.
- **LiteLLM Registry**: Secondary source for direct provider pricing (OpenAI, Anthropic, Google).
- **Hardcoded Heuristics**: Mapping known models/tiers to Intelligence and Speed scores.

## 2. Heuristics Mapping

### Intelligence (0-100)

- **100**: `o1-preview`, `claude-3-5-sonnet` (latest), `gpt-4o`.
- **90**: `claude-3-opus`, `gpt-4-turbo`.
- **70**: `llama-3.1-70b`, `claude-3-sonnet`, `gemini-1.5-pro`.
- **50**: `gpt-4o-mini`, `llama-3.1-8b`, `gemini-1.5-flash`.
- **30**: `gpt-3.5-turbo`, `haiku`.
- **Fallback**: 40.

### Speed (1-5, 5 is fastest)

- **5**: `-mini`, `-flash`, `-haiku`, Groq-hosted models.
- **3**: Standard flagship models (`4o`, `3.5-sonnet`).
- **1**: Heavy models (`opus`, `o1`, `405b`).

## 3. Implementation Plan

### 3.1 `scripts/market_explorer.py`

A standalone async script using `httpx` and `rich` to:

- Fetch and merge catalogs.
- Apply filters (`--max-price`, `--min-intel`, `--query`).
- Sort by `price`, `intel`, or `speed`.

### 3.2 CLI Integration

- Add `harnessctl models market` command.
- Reuse logic from `market_explorer.py`.

## 4. Proposed Filters

- `--name`: Substring match on model ID.
- `--max-price`: Filter by input cost per Mtok.
- `--min-intel`: Filter by intelligence score.
- `--min-speed`: Filter by speed score.
- `--sort`: `price|intel|speed|context`.

## 5. Success Criteria

- User can run a single command/script to see a ranked list of the entire market.
- Output includes clear columns for all requested metrics.
- Filtering works as expected.
