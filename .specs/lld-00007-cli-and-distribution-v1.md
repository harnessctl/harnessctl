---
id: "00007"
type: lld
title: "CLI and Distribution"
version: 1
status: draft
parent: "00001"
opencode-agent: lead-engineer
---

# CLI and Distribution

## Context

Implements **Req 3**: run the tool directly from the GitHub repo via `uvx`
(install from latest release zip or by cloning the repo), plus the user-facing
CLI surface that drives all other subsystems (LLD-00001–00006). Python + uv per
agreed decision 1.

## Approach

**CLI framework:** **Typer** (declarative, type-hint driven) for commands +
**Rich** for tables/diffs/status. Single entrypoint `harnessctl`. Command groups
map to subsystems:

```
harnessctl init                    # scaffold config root (LLD-00001)
harnessctl validate                # load + semantic validate, print warnings
harnessctl compile [--harness X] [--scope NAME ...] [--project DIR]  # render+emit content & settings (LLD-00002/03)
        [--dry-run|--diff|--check|--write]
harnessctl discover                # local runtimes/models (LLD-00004)
harnessctl models list [--sort cost|context|provider] [--refresh]  # (LLD-00004)
harnessctl models recommend <task>          # (LLD-00005)
harnessctl models pull <hf:repo|ollama:n|url>  # (LLD-00005)
harnessctl agents show             # render topology graph (LLD-00006)
harnessctl version
```

Global flags: `--config PATH`, `--home PATH` (`HARNESSCTL_HOME`), `--verbose`,
`--json` (machine output for scripting). A shared `AppContext` loads the `Spec`
once and carries the `WarningCollector`; every command flushes warnings to stderr
at exit (grouped, never silently dropped).

**Exit codes:** `0` ok; `1` runtime error; `2` validation/`SpecError`; `3`
`--check` drift detected (CI-friendly).

**Packaging / distribution:** standard PEP 621 `pyproject.toml` with
**`[project.scripts] harnessctl = "harnessctl.cli:app"`**, built by uv
(hatchling backend). Templates + default specs shipped as **package data** so a
zero-clone `uvx` run has everything.

Three run paths, all via uv:

| Path                    | Command                                                               |
| ----------------------- | --------------------------------------------------------------------- |
| From repo (HEAD)        | `uvx --from git+https://github.com/<u>/harnessctl harnessctl …`       |
| From a release tag      | `uvx --from git+https://github.com/<u>/harnessctl@<tag> harnessctl …` |
| From PyPI/release wheel | `uvx harnessctl …`                                                    |
| Cloned dev              | `uv run harnessctl …` / `uv sync`                                     |

**Release automation:** a GitHub Actions workflow on tag `v*` builds sdist+wheel
(`uv build`), attaches the zip/wheel to a GitHub Release, and (optionally)
publishes to PyPI. This satisfies "install from latest release (zip) or from
repository itself."

## File Changes

| File                            | Change                                                                                                               |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `pyproject.toml`                | `[project.scripts]` entrypoint, package-data include for `templates/` + `spec/defaults/`, uv/hatchling build config. |
| `src/harnessctl/cli.py`         | Typer `app`, global options, `AppContext`, warning-flush, exit codes.                                                |
| `src/harnessctl/commands/*.py`  | One module per command group (init, validate, compile, discover, models, agents).                                    |
| `src/harnessctl/output.py`      | Rich renderers (tables, diffs, status) + `--json` serializers.                                                       |
| `.github/workflows/release.yml` | Tag-triggered `uv build` + GitHub Release asset upload + optional PyPI publish.                                      |
| `README.md`                     | Quickstart with the `uvx` invocations.                                                                               |

## Tasks

1. Add `[project.scripts]` entrypoint + package-data config; verify wheel includes templates/defaults. (`pyproject.toml`)
2. Implement Typer `app`, `AppContext` (single Spec load), global flags, warning flush, exit-code policy. (`cli.py`)
3. Implement `init` + `validate` commands. (`commands/init.py`, `commands/validate.py`)
4. Implement `compile` command with `--harness`/`--scope`/`--project` selection and `--dry-run/--diff/--check/--write`. (`commands/compile.py`)
5. Implement `discover` + `models list/recommend/pull` commands. (`commands/discover.py`, `commands/models.py`)
6. Implement `agents show` topology render. (`commands/agents.py`)
7. Implement Rich + `--json` output layer. (`output.py`)
8. Author release workflow + README quickstart; smoke-test `uvx --from git+…`. (`.github/workflows/release.yml`, `README.md`)
9. Tests: command wiring, exit codes (esp. `--check`=3), `--json` shape, package-data presence in built wheel. (`tests/cli/`)

## Edge Cases

- **`uvx` run with no config root** — commands needing a Spec error with a hint to run `harnessctl init`; `version`/`--help` always work.
- **Package data missing from wheel** — covered by a build test asserting templates/defaults are importable resources.
- **Partial network (pull/pricing) under `uvx`** — same cache/stale-fallback behavior as LLD-00004; no special-casing.
- **`--json` + warnings** — warnings go to stderr as JSON when `--json`, keeping stdout clean for piping.
- **Windows** — out of scope v1 (Linux-first); paths use `pathlib`, so not actively broken but untested.

## Decisions

- **Typer + Rich** over argparse/click-raw — least boilerplate, typed, good UX for tables (Gemini consensus).
- **uv/uvx + git source** over npx/Node — Python ecosystem owns HF + system probing (decision 1); `uvx --from git+` gives zero-install repo runs.
- **Templates as package data** over fetch-at-runtime — `uvx` works offline after first resolve; reproducible.
- **Dedicated exit code for `--check` drift** — enables CI gating of config drift.
- **Single Spec load via AppContext** — avoids re-parsing per command; consistent warnings.

## Assumptions

- Users have `uv` installed (or install it once); `uvx` is the documented entrypoint.
- Repo will be public on GitHub at a stable path for the `uvx --from git+` URL.
- PyPI publishing is optional; GitHub Release assets satisfy the "release zip" requirement on their own.
