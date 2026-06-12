# harnessctl

`harnessctl` is the operational nerve center for your AI agent swarm. It bridges the gap between high-level architectural intent and the low-level configuration of AI harnesses like OpenCode and Pi.dev.

By enforcing a standardized **3-Tier Hub-and-Spoke Topology**, `harnessctl` ensures your agents remain cost-effective, specialized, and highly coordinated.

---

## Table of Contents

- [The Philosophy](#the-philosophy)
- [Core Concepts](#core-concepts)
  - [3-Tier Topology](#3-tier-topology)
  - [The Verdict Protocol](#the-verdict-protocol)
- [Installation](#installation)
- [Quickstart](#quickstart)
- [Specification Guide (agents.yaml)](#specification-guide-agentsyaml)
  - [Tiers & Models](#tiers--models)
  - [Agents & Roles](#agents--roles)
  - [MCP Servers](#mcp-servers)
- [Advanced Usage](#advanced-usage)
  - [The Template Engine](#the-template-engine)
  - [Model Discovery & Recommendation](#model-discovery--recommendation)
- [Command Reference](#command-reference)
- [License](#license)

---

## The Philosophy

Building complex systems with LLMs often leads to **"The Orchestration Mess"**:

1. **Model Mismatch**: Using a $30/1M token model to write unit tests.
2. **Context Bloat**: Subagents getting lost in huge prompts.
3. **Fragile Hand-offs**: Agents not knowing how to escalate problems.

`harnessctl` solves this by treating agents as **model-bound roles** with a strict communication contract.

---

## Core Concepts

### 3-Tier Topology

We organize agents into three logical capability levels:

| Tier            | Capability                                          | Example Models                         |
| :-------------- | :-------------------------------------------------- | :------------------------------------- |
| **Reasoning**   | Design docs, complex algorithms, critical review.   | `o3-mini`, `gpt-4o`, `claude-3-5-opus` |
| **Balanced**    | Implementation planning, LLDs, feature development. | `claude-3-5-sonnet`, `gpt-4o-mini`     |
| **Cheap/Local** | Boilerplate, tests, precise specs, low-latency.     | `llama3:8b`, `qwen2.5-coder`           |

### The Verdict Protocol

Agents don't just "talk"; they return **verdicts**. This allows the **Hub** (the orchestrator) to sequence work without needing to understand the content depth.

- `DONE`: Task complete.
- `APPROVED`: Validation passed.
- `CHANGES{notes: "..."}`: Revision requested.
- `ESCALATE{reason: "..."}`: Task exceeds tier capability.
- `NEEDS_SPEC{gap: "..."}`: Ambiguous instructions.

---

## Installation

`harnessctl` is managed with `uv`.

```bash
# Install directly from GitHub
uvx --from git+https://github.com/dragoscirjan/noname.git harnessctl --help

# Or for local development
git clone https://github.com/dragoscirjan/noname.git
cd noname
uv sync
```

---

## Quickstart

1.  **Initialize**: Generate your blueprint.
    ```bash
    harnessctl init
    ```
2.  **Discover**: See what's running locally.
    ```bash
    harnessctl models discover
    ```
3.  **Validate**: Ensure your topology is sound.
    ```bash
    harnessctl validate
    ```
4.  **Compile**: Push your swarm into the harness.
    ```bash
    harnessctl compile --mode write
    ```

---

## Specification Guide (`agents.yaml`)

The `agents.yaml` is the source of truth for your swarm.

### Tiers & Models

Tiers abstract away specific model IDs, allowing you to swap backends without touching agent prompts.

```yaml
tiers:
  reasoning:
    primary: gpt-4o
    fallback: o3-mini
  balanced:
    primary: claude-3-5-sonnet
```

### Agents & Roles

Agents map a role (Hub or Worker) to a capability Tier.

```yaml
agents:
  orchestrator:
    role: hub
    tier: balanced
    can_delegate: [researcher, coder]
  researcher:
    role: worker
    tier: reasoning
    escalates_to: orchestrator
```

### MCP Servers

Standardize your toolbelt across all agents.

```yaml
mcp:
  google-search:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-google-search"]
```

---

## Advanced Usage

### The Template Engine

`harnessctl` uses a priority-based inheritance system for Jinja2 templates. When compiling for an agent named `researcher` with role `worker` and tier `reasoning`:

1.  **Direct Match**: `agents/researcher.md.j2`
2.  **Role Fallback**: `agents/worker.md.j2`
3.  **Tier Fallback**: `agents/reasoning.md.j2`

### Model Discovery & Recommendation

Don't guess which model fits your GPU. `harnessctl` probes your system (VRAM, CPU) and crosses it with live pricing data to recommend the optimal tier setup.

```bash
harnessctl models recommend "Write a complex Rust backend" --tier reasoning
```

---

## Command Reference

| Command            | Description                                              |
| :----------------- | :------------------------------------------------------- |
| `init`             | Scaffold a default `agents.yaml`.                        |
| `validate`         | Load and validate the spec file (checks cycles & depth). |
| `compile`          | Render and emit configurations (OpenCode/Pi.dev).        |
| `discover`         | Scan for local runtimes (Ollama, MLX).                   |
| `agents show`      | Render the agent topology as a visual tree.              |
| `models list`      | Show all models with pricing and context windows.        |
| `models recommend` | Recommend a model for a specific task.                   |

---

## License

MIT © Dragos Cirjan
