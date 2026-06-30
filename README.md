# harnessctl: The Unified AI Agent Orchestrator

`harnessctl` is a CLI tool for managing multi-agent topologies and model propagation across different AI harnesses (e.g., OpenCode, Pi.dev). It enforces a strict **Three-Tier Hub-and-Spoke** architecture to ensure cost-efficiency, reliability, and structured communication between agents.

---

## Table of Contents

- [Why harnessctl?](#why-harnessctl)
- [The Three-Tier Architecture](#the-three-tier-architecture)
- [Configuration Reference (agents.yaml)](#configuration-reference-agentsyaml)
  - [Global Properties](#global-properties)
  - [Harness Configuration](#harness-configuration)
  - [Tiers & Model Mapping](#tiers--model-mapping)
  - [Models & Sources](#models--sources)
  - [Agent Topology](#agent-topology)
  - [MCP Servers](#mcp-servers)
- [Command Reference](#command-reference)
  - [v1 Operator Workflow](#v1-operator-workflow)
  - [Lifecycle Commands](#lifecycle-commands)
  - [Discovery & Model Intelligence](#discovery--model-intelligence)
  - [Topology Visualization](#topology-visualization)
- [The Verdict Protocol](#the-verdict-protocol)
- [Template Fallback System](#template-fallback-system)
- [Installation](#installation)

---

## Why harnessctl?

Managing AI agents is hard because of **Model Mismatch** (using expensive models for cheap tasks) and **Orchestration Drift** (configurations becoming inconsistent across different IDEs or environments).

`harnessctl` solves this by:

1.  **Standardizing** how agents are defined and how they communicate.
2.  **Propagating** model choices, toolsets (MCP), and prompts to multiple harnesses from a single source of truth.
3.  **Adapting** to your hardware by recommending the best models for your local RAM/VRAM.

---

## The Three-Tier Architecture

`harnessctl` defaults to a **Hub-and-Spoke** topology where one "Balanced" Hub orchestrates specialized workers:

| Tier            | Role               | Typical Models               | Use Case                                                |
| :-------------- | :----------------- | :--------------------------- | :------------------------------------------------------ |
| **Reasoning**   | The "Thinker"      | `gpt-4o`, `o3-mini`, `r1`    | Complex design, logic, and critical reviews.            |
| **Balanced**    | The "Orchestrator" | `claude-3-5-sonnet`          | Routing, sequencing, and standard implementation.       |
| **Cheap/Local** | The "Worker"       | `llama3:8b`, `qwen2.5-coder` | Boilerplate, unit tests, and well-defined coding tasks. |

---

## Configuration Reference (`agents.yaml`)

The `agents.yaml` file is divided into several logical sections. Below is an exhaustive list of all properties with examples.

### Global Properties

- `version`: (String) The spec version. Usually "1.0".

### Harness Configuration

Define where and how configurations are emitted.

```yaml
harness:
  opencode: # Harness ID
    capabilities:
      supports_subagent_model: true # If false, harnessctl injects model name into the prompt
      supports_tool_permissions: full # Options: full, partial, none
      supports_mcp: true
    scopes:
      - name: global
        kind: global # Options: global, project, custom
        path: "~/.config/opencode"
      - name: local
        kind: project
        path: "{project}/.opencode" # {project} resolves to the current project dir
```

### Tiers & Model Mapping

Map logical tiers to specific model identifiers.

```yaml
tiers:
  reasoning:
    primary: gpt-4o
    fallback: o3-mini # Optional
  balanced:
    primary: claude-3-5-sonnet
```

### Models & Sources

Exhaustive definition of where models come from.

```yaml
models:
  gpt-4o:
    sources:
      - via: openai # Options: openai, anthropic, openrouter, ollama, mlx, etc.
        id: gpt-4o
        key_ref: OPENAI_API_KEY # Env var name
  llama3:
    sources:
      - via: ollama
        id: llama3:8b
        base_url: "http://localhost:11434"
```

### Agent Topology

Define your agents and how they relate.

```yaml
agents:
  hub:
    role: hub # Options: hub, worker
    tier: balanced
    can_delegate: [researcher, coder] # List of worker names
  researcher:
    role: worker
    tier: reasoning
    escalates_to: hub # The agent to return to if overwhelmed
  coder:
    role: worker
    tier: cheap_local
    delegate_via: cli # (Optional) "cli" for out-of-process execution
```

### MCP Servers

Configure Model Context Protocol servers.

```yaml
mcp:
  google-search:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-google-search"]
    env:
      GOOGLE_API_KEY: "..."
    disabled: false # (Optional) Default: false
```

---

## Command Reference

### v1 Operator Workflow

For the v1 operator commands and MCP decision contract examples, use:

- `docs/operators/v1-operator-guide.md`
- `docs/verification/issue-23-operator-docs-repro.md`

This workflow covers:

- `config init`
- `prompts install`
- `prompts render`
- `mcp select_model_for_task`
- schema validation failures and remediation.

### Lifecycle Commands

#### `init`

Scaffold a default `agents.yaml` spec file.

```bash
# Creates agents.yaml in the current directory
harnessctl init

# Create with a custom name
harnessctl init --config my-swarm.yaml
```

#### `validate`

Perform a deep semantic check of your spec.

```bash
# Validates cycles, tier resolution, and harness capabilities
harnessctl validate
```

#### `compile`

The core engine. Renders prompts and generates config files.

```bash
# Write configs to all enabled harnesses
harnessctl compile --mode write

# Preview changes without writing (shows diffs)
harnessctl compile --mode diff

# Run in CI to check if configs are in sync with spec
harnessctl compile --mode check # Exits with code 3 if drift detected
```

### Discovery & Model Intelligence

#### `discover`

Probe the local system for running Ollama or MLX instances.

```bash
harnessctl discover
```

#### `models list`

Show a unified view of all existing models on the market and those discovered locally. Includes **Intelligence**, **Speed**, and **Price** metrics.

```bash
# List all models (commercial + local), sorted by intelligence
harnessctl models list

# Filter for local models only (Ollama, MLX, LM Studio)
harnessctl models list --local

# Filter for commercial models only (OpenRouter)
harnessctl models list --commercial

# Sort by speed and filter by name
harnessctl models list --sort-by speed --grep claude
```

**Metrics Explanation:**

- **Intelligence**: Normalized 0-100 score based on **Artificial Analysis** and **LMSYS** benchmarks.
- **Speed**: Represented as **Tokens Per Second (TPS)**. Commercial data is pulled from provider medians; local speed is estimated based on model parameters.
- **Price**: Real-time USD per 1 Million tokens (Input/Output).

**Local Tool Detection:**
Before listing, `harnessctl` probes for active local services. It reports status for:

- **Ollama** (Port 11434)

* **LM Studio** (Port 1234)
* **Llama.cpp** (Port 8080)
* **MLX** (Mac only, process check)

#### `models recommend`

Recommend the best HuggingFace/Local model based on your system's RAM/VRAM.

```bash
harnessctl models recommend "Write a distributed database in Rust"
```

### Topology Visualization

#### `agents show`

Render the agent delegation tree in your terminal.

```bash
harnessctl agents show
```

---

## The Verdict Protocol

Agents don't just provide text; they are prompted to conclude with a structured **Verdict**. This is the key to the Hub-and-Spoke model.

1.  **DONE**: Success. No further action.
2.  **APPROVED**: Review passed. Artifact accepted.
3.  **CHANGES{notes: "..."}**: Specific feedback for revision.
4.  **ESCALATE{reason: "..."}**: Too complex for current tier. Orchestrator reroutes to a higher tier.
5.  **NEEDS_SPEC{gap: "..."}**: Instructions were ambiguous. Orchestrator refines and redispatches.

---

## Template Fallback System

Prompts are rendered using Jinja2. `harnessctl` searches for templates in this order:

1.  **Agent Specific**: `agents/researcher.md.j2`
2.  **Role Generic**: `agents/worker.md.j2`
3.  **Tier Generic**: `agents/reasoning.md.j2`

This allows you to define one "Reasoning Worker" prompt that applies to all thinkers, while overriding it only when a specific agent needs unique instructions.

---

## Installation

```bash
# Standard install via uv
uv tool install git+https://github.com/dragoscirjan/noname.git

# Run directly without installing
uvx --from git+https://github.com/dragoscirjan/noname.git harnessctl
```

---

## License

MIT © Dragos Cirjan
