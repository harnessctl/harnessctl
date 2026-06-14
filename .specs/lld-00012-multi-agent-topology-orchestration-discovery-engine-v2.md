# LLD-00012: Multi-Agent Topology Orchestration & Discovery Engine

## Overview
This LLD defines the mechanisms for managing complex multi-agent setups (topologies) using a compositional configuration approach (Jsonnet) and an automated Discovery Engine that scans for agent dependencies (skills) within instruction templates.

## Architecture

### 1. Topology Configuration (Compositional Setup)
We transition from flat YAML to a hierarchical configuration using **Jsonnet**.
- **Base Components**: Define standard agent profiles (e.g., `coder`, `reviewer`, `architect`) as reusable functions.
- **Mixins**: Allow adding common capabilities (e.g., `with-git`, `with-mcp`) to any agent.
- **Topology Manifest**: A `.jsonnet` file that describes the entire team, their roles, and their connectivity.

**Key File**: `src/harnessctl/topology/loader.py`
- Handles `.jsonnet` evaluation and conversion to the internal YAML/JSON spec.
- Supports variable injection (e.g., project name, budget limits).

### 2. Discovery Engine (Static Skill Scanning)
The Discovery Engine proactively identifies what "skills" an agent needs by scanning its instruction templates (Jinja2) before execution.

**Tag Pattern**: `{% load_skill skills="clean-code, developer-backend" %}`
- This tag is placed at the top of a Markdown template.
- The Discovery Engine extracts these skill names and ensures they are loaded/available in the agent's environment.

**Key File**: `src/harnessctl/discovery/engine.py`
- Function `scan_template(template_path: Path) -> List[str]`.
- Logic to cross-reference discovered skills with the available skills in the `.opencode/skills` or `~/.config/opencode/skills` directories.

### 3. Orchestration Flow
1. **Topology Loading**: `harnessctl topology create <name> --config my-team.jsonnet`.
2. **Expansion**: Jsonnet expands the manifest into a concrete list of agents and their settings.
3. **Static Discovery**: For each agent, its referenced template is scanned for `load_skill` tags.
4. **Environment Preparation**: The harness (OpenCode or Pi) is bootstrapped with the required skills, models (via the recommendation engine), and MCP tools.
5. **Output**: A finalized `opencode.json` or `pi-config.yml` is generated.

## Implementation Details

### Jsonnet Wrapper (`src/harnessctl/topology/jsonnet.py`)
- Wrapper around `go-jsonnet` (or `python-jsonnet`) to provide native function calls for hardware probing.
- Allows the configuration to be hardware-aware: `if sysprobe.vram_gb > 8 then "local" else "cloud"`.

### Template Scanner (`src/harnessctl/discovery/scanner.py`)
- Regex-based extraction of `load_skill` tags.
- Validation: Warn if a requested skill is missing from the local skill library.

## Verification Plan
1. **Jsonnet Evaluation**: Test `harnessctl topology create` with a complex `.jsonnet` that uses imports and mixins.
2. **Skill Discovery**: Create a template with `{% load_skill skills="test-skill" %}` and verify it appears in the generated config's `skills` array.
3. **Hardware Awareness**: Verify that a Jsonnet config can correctly branch its model selection based on `sysprobe` data injected into the VM.
