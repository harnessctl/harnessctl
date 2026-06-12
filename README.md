# harnessctl

`harnessctl` is a unified CLI utility designed to manage AI harness configurations, agent topologies, and MCP servers across different environments (like OpenCode and Pi.dev). It simplifies the orchestration of agent templates, model selection, and multi-tier delegation strategies.

## Key Features

- **Agent Topology Management:** Define and validate Hub-and-Spoke hierarchies with multi-tier delegation.
- **Multi-Harness Support:** Emit configurations tailored for specific AI harnesses (OpenCode, Pi.dev, etc.).
- **Model Intelligence:** Automated model recommendation based on hardware discovery and pricing (LiteLLM, OpenRouter).
- **Template Orchestration:** Render smart prompt templates with built-in escalation protocols and model injection.
- **MCP Server Management:** Centralized configuration of Model Context Protocol (MCP) servers.

## Installation

`harnessctl` is built with Python 3.12+ and managed with `uv`.

```bash
# Clone the repository
git clone https://github.com/dragoscirjan/noname.git
cd noname

# Install dependencies and build
uv sync
uv build
```

## Usage

### 1. Initialization

Start by scaffolding a default specification file.

```bash
harnessctl init
```

This creates an `agents.yaml` file in your current directory.

### 2. Specification Management

The `agents.yaml` file defines your tiers, models, agents, and MCP servers. You can validate your configuration at any time:

```bash
harnessctl validate
```

This checks for schema errors, circular delegations, and missing model references.

### 3. Agent Topology

Visualize your agent hierarchy to ensure correct delegation and escalation paths.

```bash
harnessctl agents show
```

### 4. Configuration Compilation

Render and emit the configuration to your target harnesses.

```bash
# Dry run to see what would change
harnessctl compile --mode dry-run

# Write the configurations
harnessctl compile --mode write
```

Depending on your `agents.yaml`, this will update files like `opencode.json`, `settings.json`, and render agent/skill templates into the appropriate directories.

### 5. Model Discovery & Recommendation

`harnessctl` can discover local runtimes (like Ollama or MLX) and recommend the best model for your hardware.

```bash
# Discover local models
harnessctl models discover

# Get a recommendation for a balanced task
harnessctl models recommend "coding task" --tier balanced
```

## Command Reference

| Command            | Description                                           |
| :----------------- | :---------------------------------------------------- |
| `init`             | Create a boilerplate `agents.yaml`.                   |
| `validate`         | Check the spec for errors and warnings.               |
| `compile`          | Render templates and settings to harness directories. |
| `discover`         | Scan for local LLM runtimes (Ollama/MLX).             |
| `agents show`      | Display the agent delegation tree.                    |
| `models list`      | List all models available in the current spec.        |
| `models recommend` | Suggest the best model based on tier and hardware.    |

## Configuration Example (`agents.yaml`)

```yaml
version: "1.0"

tiers:
  reasoning:
    primary: gpt-4o
    fallback: gpt-4-turbo
  balanced:
    primary: claude-3-5-sonnet
    fallback: gpt-4o-mini
  cheap_local:
    primary: llama3:8b
    local_only: true

agents:
  hub:
    role: hub
    tier: balanced
    can_delegate: [researcher, coder]
  researcher:
    role: worker
    tier: reasoning
    escalates_to: hub
  coder:
    role: worker
    tier: balanced
    escalates_to: hub

mcp:
  google-search:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-google-search"]
```

## License

MIT
