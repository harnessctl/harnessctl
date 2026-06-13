# LLD-00013: Hybrid Intent-Aware Model Recommendation Engine

## Overview
Transform `harnessctl models recommend` from a static keyword-based tool into an intent-aware recommender that balances local hardware constraints against commercial cloud capabilities.

## Architecture

### 1. Intent Analyzer (`src/harnessctl/recommend/intent.py`)
Parses the user sentence into a `TaskIntent` object.
- **Complexity Score (1-100)**: 
    - Low (1-30): Single scripts, basic QA, summaries.
    - Med (31-70): Multi-step tasks, refactoring, specific libraries.
    - High (71-100): Architecture, multi-service systems, complex auth, reasoning.
- **Domain Focus**: `coding`, `reasoning`, `creative`, `general`.
- **Requirements**: `speed`, `accuracy`, `privacy`.

**Implementation Strategy**: Simple keyword/regex-based scoring initially (e.g., "microservice", "auth", "architecture" -> high complexity).

### 2. Market-Aware Scorer (`src/harnessctl/recommend/ranker.py`)
Integrates data from `MarketModel` (from `pricing/market.py`).
- **Intelligence Alignment**: 
    - If `Complexity > 70`, prioritize models with `Intelligence > 90` (e.g., Gemini 1.5 Pro, Claude 3.5 Sonnet).
    - If `Complexity < 30`, prioritize fast/local models (e.g., Llama 3.2 3B).
- **Cost/Speed Weighting**: Apply user preferences for speed vs. cost.

### 3. Allocation Strategy
- **Local (VRAM)**: Best for privacy and zero-cost. Recommended for Low/Med complexity if it fits.
- **Cloud (Commercial)**: Recommended when:
    - Task complexity exceeds local model capabilities.
    - Local memory is insufficient.
    - High accuracy/SOTA reasoning is required (e.g., your AWS Cognito example).

## Changes

### `src/harnessctl/recommend/intent.py` (New)
- Class `TaskIntent`: `complexity`, `tags`, `keywords`.
- Function `analyze_intent(task: str) -> TaskIntent`.

### `src/harnessctl/recommend/ranker.py`
- Update `search_candidates` to accept `TaskIntent`.
- Fetch data from `MarketProvider` to include Cloud models in the pool.
- Score function: `FinalScore = (Intelligence * 0.6) + (Alignment * 0.4)`.

### `src/harnessctl/commands/models.py`
- Wire `analyze_intent` into `recommend_cmd`.
- Add `--local / --no-local` and `--commercial / --no-commercial` boolean flags (default: both True).
- Display separate sections for "Local (Free)" and "Cloud (SOTA)".

## Verification Plan
1. `harnessctl models recommend "hello world"` -> Recommend 3B/8B local models.
2. `harnessctl models recommend "Write a typescript microservice with AWS congnito"` -> Recommend SOTA Cloud models (Gemini/Claude).
3. Verify memory estimations remain accurate for local GGUF models.
