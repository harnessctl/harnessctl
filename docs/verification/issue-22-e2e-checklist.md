# Issue #22 — End-to-End Manual Verification Checklist

Date: 2026-06-30
Repo: `harnessctl/harnessctl`
Branch: `feat/issue-22-manual-verification-checklist`

## Environment

- Clean test home: `/tmp/opencode/issue22/home`
- Clean test project: `/tmp/opencode/issue22/project`
- Runtime command wrapper: `mise exec -- uv run harnessctl ...`

---

## 1) Config init (global)

### Command

```bash
HARNESSCTL_HOME="/tmp/opencode/issue22/home" \
mise exec -- uv run harnessctl config init --provider github-copilot --global
```

### Observed output

```text
Initialized config:
- /tmp/opencode/issue22/home/config.yaml
```

### Expected result

- `config.yaml` is created under harnessctl-managed global directory.

---

## 2) Config tweak (manual edit)

Updated `/tmp/opencode/issue22/home/config.yaml` to verify non-default behavior:

- added task class `frontend`
- added alias `ui: frontend`
- added `frontend-rule` optimizing for `cost_per_success`

### Expected result

- MCP decision path can resolve `task_type=ui` via taxonomy alias and match `frontend-rule`.

---

## 3) MCP decision (`select_model_for_task`)

### Command

```bash
mise exec -- uv run harnessctl mcp select_model_for_task \
  --request-json '{"prompt":"Implement new button states","task_type":"ui","constraints":{"provider_allowlist":["github-copilot"]}}' \
  --config-file "/tmp/opencode/issue22/home/config.yaml" \
  --pretty
```

### Observed highlights

- `selected_agent: "copilot-default"`
- `selected_model: "github-copilot/gpt-5-mini"`
- `trace.matched_rules: ["frontend-rule"]`
- `trace.derived.task_class: "frontend"`
- `trace.provenance.task_class: "caller_hint_alias"`

### Expected result

- Agent-first contract is returned.
- Derived metadata + provenance are present.
- Rule/objective selection reflects config tweak.

---

## 4) Prompts install (global single harness)

### Command

```bash
HARNESSCTL_HOME="/tmp/opencode/issue22/home" \
mise exec -- uv run harnessctl prompts install --global --harness opencode --version v1
```

### Observed output

```text
Installed prompt bundles:
- /tmp/opencode/issue22/home/prompts/opencode/v1/orchestrator.md
```

### Expected result

- Prompt bundle file is created under harnessctl-managed global prompts path.

---

## 5) Prompts install (project multi-harness)

### Command

```bash
mise exec -- uv run harnessctl prompts install \
  --project "/tmp/opencode/issue22/project" \
  --harness pi \
  --harness opencode \
  --version v1
```

### Observed output

```text
Installed prompt bundles:
- /tmp/opencode/issue22/project/.harnessctl/prompts/pi/v1/orchestrator.md
- /tmp/opencode/issue22/project/.harnessctl/prompts/opencode/v1/orchestrator.md
```

### Expected result

- Both harness bundles are created under project-local harnessctl-managed path.

---

## 6) Prompts render (no-write stdout)

### Command

```bash
mise exec -- uv run harnessctl prompts render \
  --harness opencode \
  --harness pi \
  --version v1 \
  --cli \
  --var tone=direct
```

### Observed output

- Printed two markdown prompt sections (opencode + pi) to stdout.
- Includes injected variable line: `tone: direct`.

### No-write verification

Directory listings after render remained constrained to install outputs:

- `/tmp/opencode/issue22/home`: `config.yaml`, `prompts/`
- `/tmp/opencode/issue22/project/.harnessctl`: `prompts/`

No additional files were produced by `prompts render` itself.

---

## Common Failure Diagnostics (captured)

### A) MCP provider allowlist conflict

Command (allowlist excludes configured provider):

```bash
mise exec -- uv run harnessctl mcp select_model_for_task \
  --request-json '{"prompt":"Implement endpoint","task_type":"implementation","constraints":{"provider_allowlist":["openrouter"]}}' \
  --config-file "/tmp/opencode/issue22/home/config.yaml" \
  --pretty
```

Observed error payload:

```json
{
  "error": {
    "code": "PROVIDER_BLOCKED",
    "message": "No candidates left after provider allowlist gate.",
    "details": {
      "gate": "provider_allowlist",
      "allowlist": ["openrouter"]
    }
  }
}
```

### B) Prompts install collision without overwrite

Command (re-run same install without `--overwrite`):

```bash
HARNESSCTL_HOME="/tmp/opencode/issue22/home" \
mise exec -- uv run harnessctl prompts install --global --harness opencode --version v1
```

Observed diagnostic:

```text
Refusing to overwrite existing files (use --overwrite):
- /tmp/opencode/issue22/home/prompts/opencode/v1/orchestrator.md
```

### C) Prompts render without `--cli`

Command:

```bash
mise exec -- uv run harnessctl prompts render --harness opencode --version v1
```

Observed diagnostic:

```text
prompts render currently requires --cli
```

---

## Conclusion

The full v1 workflow passes manual verification:

1. `config init` works in clean global environment.
2. Manual config tweak is honored by MCP decision path.
3. MCP contract returns agent-first response and trace/provenance.
4. `prompts install` works for global single harness and project multi-harness.
5. `prompts render` outputs to stdout with variable injection and no filesystem writes.
6. Expected failure diagnostics are clear and actionable.
