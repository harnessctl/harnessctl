---
id: "00011"
type: lld
title: "Unified Model Recommendation Engine"
version: 1
status: draft
opencode-agent: lead-engineer
---

# Unified Model Recommendation Engine

## Overview
Expand `harnessctl` to provide intelligent model recommendations by balancing intelligence, speed, and cost across local and commercial providers.

## Goals
- Unified scoring of Local and Commercial models.
- Support for "Task Profiles" (e.g., Coding, Reasoning, Chat, Fast).
- Hardware-aware local model filtering.
- CLI command `harnessctl recommend`.

## Task Profiles
| Profile | Focus | Intelligence Weight | Speed Weight | Price Weight |
| :--- | :--- | :--- | :--- | :--- |
| `coding` | Capabilities | 1.5 | 0.8 | 1.0 |
| `reasoning` | Deep Thought | 2.0 | 0.5 | 1.0 |
| `chat` | Balanced | 1.0 | 1.0 | 1.0 |
| `fast` | Responsiveness | 0.5 | 2.0 | 0.8 |

## Logic

### 1. Data Aggregation
- Use `MarketAggregator` (market.py) to fetch global models.
- Use `UnifiedDiscovery` (discovery/status.py) to find local models.
- Merge using `merge_market_data` (catalog.py).

### 2. Hardware Filtering (Local)
- Local models that require more RAM/VRAM than available (using `estimate_footprint`) are excluded unless already running.

### 3. Scoring Formula
```python
# Values normalized between 0.0 and 1.0
norm_intel = intelligence / 100.0
norm_speed = min(speed_tps, 200) / 200.0
# Price is inverted: lower price = higher score. 0.0 is best.
# We use log scale for price to handle range from 0 to $100+/mtok
norm_price = 1.0 - (math.log10(price + 0.01) + 2) / 4  

score = (norm_intel ** i_weight) * (norm_speed ** s_weight) * (norm_price ** p_weight)
```

## Implementation Plan

### 1. Engine (`src/harnessctl/recommend/engine.py`)
- Define `RecommendationEngine` class.
- Implement profile weights.
- Integrate `SystemProfile` for memory checks.

### 2. CLI (`src/harnessctl/commands/recommend.py`)
- Arguments:
    - `profile`: [coding, reasoning, chat, fast] (default: chat)
    - `--limit`: Number of results (default: 5)
    - `--local-only` / `--commercial-only`
    - `--max-price`: Maximum output price per MTok.

### 3. Formatting
- Display results in a rich table showing:
    - Model ID
    - Provider
    - Intel Score
    - Speed (est)
    - Price (MTok)
    - "Value" Score

## Affected Files
- `src/harnessctl/commands/recommend.py` (New)
- `src/harnessctl/recommend/engine.py` (New)
- `src/harnessctl/recommend/ranker.py` (Deprecated/Replaced)

