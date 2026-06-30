# Issue 23 — operator docs reproducibility check

This verification confirms `docs/operators/v1-operator-guide.md` was followed from a clean workspace.

## Environment

- Repo: `harnessctl/harnessctl`
- Workspace root: `/tmp/opencode/issue23`
- Home override: `/tmp/opencode/issue23/home`
- Project path: `/tmp/opencode/issue23/project`

## Commands run and outcomes

1. Bootstrap config (global)

```bash
HARNESSCTL_HOME=/tmp/opencode/issue23/home \
  uvx --no-cache --from . harnessctl config init --provider github-copilot --global
```

Observed:

```text
Initialized config:
- /tmp/opencode/issue23/home/config.yaml
```

2. Install prompts (global single harness)

```bash
HARNESSCTL_HOME=/tmp/opencode/issue23/home \
  uvx --no-cache --from . harnessctl prompts install --global --harness opencode --version v1
```

Observed:

```text
Installed prompt bundles:
- /tmp/opencode/issue23/home/prompts/opencode/v1/orchestrator.md
```

3. Install prompts (project multi-harness)

```bash
uvx --no-cache --from . harnessctl prompts install \
  --project /tmp/opencode/issue23/project \
  --harness pi --harness opencode --version v1
```

Observed:

```text
Installed prompt bundles:
- /tmp/opencode/issue23/project/.harnessctl/prompts/pi/v1/orchestrator.md
- /tmp/opencode/issue23/project/.harnessctl/prompts/opencode/v1/orchestrator.md
```

4. Render prompts (no-write)

```bash
uvx --no-cache --from . harnessctl prompts render \
  --harness opencode --harness pi --version v1 --var tone=direct --cli
```

Observed:

- Prompt sections printed to stdout for both harnesses.
- No file writes triggered by render.

5. MCP command with request file

```bash
uvx --no-cache --from . harnessctl mcp select_model_for_task \
  --request-file /tmp/opencode/issue23/request.json \
  --config-file /tmp/opencode/issue23/home/config.yaml --pretty
```

Observed:

- Structured JSON response returned.
- In this run, response code was `BUDGET_BLOCKED` (expected valid policy failure shape with `error` + `trace`).

6. Schema validation error example

```bash
uvx --no-cache --from . harnessctl mcp select_model_for_task \
  --request-file /tmp/opencode/issue23/request.json \
  --config-file /tmp/opencode/issue23/bad-config.yaml
```

Observed:

```text
Config validation failed: Schema validation failed at 'spec': 'routing' is a required property
```

## Conclusion

- Operator guide commands are reproducible from a clean workspace.
- Success and failure paths match documented behavior.
