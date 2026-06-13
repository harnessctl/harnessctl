# LLD-00012: Recommendation Engine & Topology Orchestration

## Overview
The `harnessctl recommend` command is the core "intelligence" of the utility. It analyzes the user's local hardware (VRAM, RAM, CPU) and the current LLM market to suggest an optimal distribution of agents across local and cloud resources.

## Core Logic: The Recommendation Algorithm

### 1. Hardware Profiling
- **Apple Silicon (MLX)**: Detect Unified Memory (RAM). Calculate usable VRAM (typically 75% of RAM).
- **NVIDIA (CUDA)**: Detect total VRAM across all GPUs.
- **CPU**: Fallback for small models if VRAM is insufficient.

### 2. Topology Types
Recommendations are grouped by "Intent":
- **Efficiency**: Maximize local execution to minimize cost. 
- **Performance**: SOTA models for reasoning, local models for tasks.
- **Balanced**: A mix of local and cloud models.

### 3. Allocation Strategy (Bin Packing)
1. **Critical Path**: Assign "Architect" or "Lead" agents to the highest Intelligence (SOTA) cloud models (e.g., GPT-4o, Claude 3.5).
2. **Worker Nodes**: Assign "Coder" or "Reviewer" agents to local models if they fit in VRAM (e.g., Llama-3-8B, Qwen-2.5-Coder).
3. **Local Capacity Check**:
    - If `sum(model_weights_fp16) < usable_vram`: All workers local.
    - Else: Move workers to cheapest cloud providers (Groq, DeepSeek).

## Command Interface

```bash
harnessctl recommend [TOPOLOGY_FILE] [OPTIONS]
```

### Options:
- `--intent [efficiency|performance|balanced]`: Default: `balanced`.
- `--budget [$/hr]`: Maximum hourly cost.
- `--local-only`: Suggest only what fits in current hardware.

## Data Structures

### Market Context
Uses the merged catalog from `fetch_market_data()` to find:
- Best Intelligence/Price ratio.
- Fastest models for task agents.

### Recommendation Output
A JSON or Table view showing:
- Agent Name -> Model ID -> Provider.
- Estimated Cost ($/hr).
- Total VRAM Pressure (MB).
- Expected Latency (Heuristic).

## Implementation Plan

1. **Hardware Utility**: Create `src/harnessctl/hardware/detector.py` to get RAM/VRAM.
2. **Scoring Engine**: Logic to rank models for specific agent roles (Coder, Architect, etc).
3. **Topology Resolver**: The bin-packing logic that matches hardware + budget to models.
4. **CLI**: Implementation of the `recommend` command using `Rich` for a clean dashboard view.
