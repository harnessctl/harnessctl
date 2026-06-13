---
id: "00010"
type: lld
title: "Unified Model Market & Local Discovery"
version: 1
status: draft
opencode-agent: lead-engineer
---

# LLD-00010: Unified Model Market & Local Discovery

This LLD defines the implementation of the `harnessctl models list` command, integrating global commercial market data with local inference tool discovery. It ensures cross-platform support (Linux/Mac) and provides the specific metrics (Intelligence, Speed, Price) requested by the user.

## 1. Local Tool Discovery (Linux & Mac)

The tool must detect the status of local inference engines before listing models.

| Tool | Detection Method | Default Port | Platform |
| :--- | :--- | :--- | :--- |
| **Ollama** | `GET http://localhost:11434/api/tags` | 11434 | Linux, Mac |
| **LM Studio** | `GET http://localhost:1234/v1/models` | 1234 | Mac (Linux beta) |
| **Llama.cpp** | `GET http://localhost:8080/health` | 8080 | Linux, Mac |
| **MLX (Server)** | `GET http://localhost:8080/v1/models` + Process check for `mlx_lm.server` | 8080 | Mac |

### Status Reporting
- **Active**: Tool responded to API call.
- **Started**: Process found, but API not responding yet.
- **Inactive**: No process or API response.

> **Resilience Rule**: If local services are inactive or fail to respond, the command **MUST NOT** exit with an error. Instead, it should print a clear warning/status header and continue to list whatever data is available (e.g., commercial models or cached local definitions).

## 2. Commercial Market Data

Data is aggregated from multiple external sources to provide a "Market View".

### Data Sources
1. **OpenRouter API**: Primary for `id`, `name`, `pricing`, and `benchmarks` (Intelligence Index).
2. **Artificial Analysis (Cached)**: Source for `Tokens Per Second (TPS)` and `Latency` metrics per provider.
3. **WhatLLM/LMSYS (Static Mapping)**: Quality scores for major models not covered by OpenRouter benchmarks.

### Unified Metrics
- **Intelligence**: Normalized 0-100 score. Priority: OpenRouter Benchmarks > Artificial Analysis Quality Index > Tier Heuristics.
- **Speed**: Represented as TPS (Tokens Per Second). Priority: Artificial Analysis Provider Median > Heuristics (e.g., Flash=150, Flagship=60, Reasoning=10).
- **Price**: USD per 1M tokens (Input/Output). Local models are always $0.00.

## 3. CLI Command: `models list`

### Arguments
- `--local`: Filter to show only models available via active local tools.
- `--commercial`: Filter to show only commercial API models.
- `--sort-by <intelligence|speed|price|context>`: Sort order.
- `--direction <asc|desc>`: Sort direction (default: desc for intel/speed, asc for price).
- `--grep <pattern>`: Case-insensitive name filter.

### UI Requirements
- Use `rich.table` for output.
- **Header**: Summary of detected local tools and their status.
- **Columns**: `Model ID`, `Source/Provider`, `Intel`, `Speed`, `Price (1M In/Out)`, `Context`.
- **Color Coding**:
    - Intel > 80: Green
    - Price > $10/1M: Red
    - Status Active: Bold Blue

## 4. Implementation Details

### 4.1 Caching Strategy
- Store market data in `~/.cache/harnessctl/market_data.json`.
- Refresh interval: 24 hours (can be forced with `--refresh`).

### 4.2 Cross-Platform Compatibility
- Use `psutil` for cross-platform process discovery.
- Use `httpx` for asynchronous API health checks.
- Detect OS via `platform.system()` to toggle MLX-specific logic on Mac.

