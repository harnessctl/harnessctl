# harnessctl v1 operator guide

This guide documents the v1 operator workflow using a single `config.yaml` plus prompt bundle commands.

## 1) Bootstrap config

Global config:

```bash
harnessctl config init --provider github-copilot --global
```

Project config:

```bash
harnessctl config init --provider openrouter --project .
```

Expected output:

```text
Initialized config:
- <target>/config.yaml
```

Notes:

- Exactly one target is required: `--global` or `--project <path>`.
- `--provider` is required.
- Existing file collisions fail by default; pass `--overwrite` to replace.

## 2) Install prompt bundles (writes files)

Global single harness:

```bash
harnessctl prompts install --global --harness opencode --version v1
```

Project multi-harness:

```bash
harnessctl prompts install --project /path/to/project --harness pi --harness opencode --version v1
```

Expected output:

```text
Installed prompt bundles:
- <target>/prompts/<harness>/<version>/orchestrator.md
```

Behavior:

- Supports repeatable `--harness`.
- Supports `--overwrite`.
- Default overwrite policy is fail-if-exists.
- Writes only under harnessctl-managed paths:
  - global: `~/.config/harnessctl/prompts/...`
  - project: `<project>/.harnessctl/prompts/...`

## 3) Render prompt bundles (no-write output)

```bash
harnessctl prompts render --harness opencode --harness pi --version v1 --var tone=direct --cli
```

Expected behavior:

- Prints rendered prompt sections to stdout.
- Does not write files.
- `--cli` is mandatory for render mode.
- Template variables are passed as repeatable `--var KEY=VALUE`.

## 4) MCP decision contract (`select_model_for_task`)

Request file example (`request.json`):

```json
{
  "prompt": "Design frontend task orchestration",
  "task_type": "frontend",
  "constraints": { "max_cost_usd": 0.5 },
  "hints": { "complexity": 40 },
  "context": { "estimated_context_size": "medium" }
}
```

Command:

```bash
harnessctl mcp select_model_for_task \
  --request-file ./request.json \
  --config-file ~/.config/harnessctl/config.yaml \
  --pretty
```

Success response is agent-first and includes:

- `selected_agent` (authoritative)
- `selected_model`, `selected_provider`, `selected_tier`
- `fallback_agents`
- `trace` (policy checks, matched rules, derived metadata, provenance)

Failure response includes:

- `error.code`
- `error.message`
- `error.details`
- `trace.derived` and `trace.provenance`

## 5) Schema/config validation failures and remediation

Common errors and fixes:

1. Missing required config sections

Example:

```text
Config validation failed: Schema validation failed at 'spec': 'routing' is a required property
```

Fix:

- Ensure `spec.routing` exists in `config.yaml`.

2. Unsupported harness

Example:

```text
Unsupported harness 'x'. Supported values: claude-cli, copilot-cli, opencode, pi
```

Fix:

- Use one of the supported harness identifiers.

3. Unsafe version value

Fix:

- Use a simple segment such as `v1`.
- Do not include separators (`/`, `\`), path traversal (`..`), or absolute paths.

4. Request/config path errors

Fix:

- For `--request-file` and `--config-file`, pass an existing regular file.

5. Policy-gate failures in MCP decisioning

Possible codes:

- `PROVIDER_BLOCKED`
- `CAPABILITY_BLOCKED`
- `RISK_BLOCKED`
- `BUDGET_BLOCKED`
- `NO_CANDIDATE_MATCH`

Fix:

- Adjust request constraints and/or config (`agent_registry`, policies, routing rules, costs) so at least one candidate survives hard gates.
