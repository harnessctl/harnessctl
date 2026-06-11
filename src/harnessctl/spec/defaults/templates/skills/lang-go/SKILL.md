---
name: lang-go
description: Go development standards, Effective Go, and tooling.
---

# GO Standards

- **Style:** [Effective Go](https://go.dev/doc/effective_go) & Google Go Style.
- **Tooling:** `gofmt` / `goimports`, `golangci-lint`, `testing` package + table-driven tests.
- **Errors:** Return errors explicitly, never panic. Wrap errors with `fmt.Errorf("%w", err)`.
- **Interfaces:** Accept interfaces, return concrete types. Keep interfaces small (1-2 methods).
- **Concurrency:** Use goroutines and channels, but avoid sharing memory to communicate; share memory by communicating.
- **Context:** Pass `context.Context` as the first argument for functions doing I/O.

Always load `clean-code` alongside this skill.
