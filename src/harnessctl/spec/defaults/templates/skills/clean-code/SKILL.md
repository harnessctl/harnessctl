---
name: clean-code
description: Clean code principles, SOLID, design patterns, readability, error handling, and universal quality tooling. Load when writing or reviewing code.
---

# Clean Code & Design Principles

## Readability

- Code should read like well-written prose — clear intent at every level
- Use meaningful, descriptive names for variables, functions, classes, and modules
- Keep functions short and focused — each function does one thing well
- Avoid deep nesting — extract early returns, guard clauses, and helper functions
- Write meaningful comments for _why_, not _what_ — the code itself should explain the what

## Clean Code Principles

- **KISS** — Keep It Simple. Prefer the simplest solution that works correctly.
- **DRY** — Don't Repeat Yourself. Extract shared logic, but don't over-abstract prematurely.
- **YAGNI** — You Aren't Gonna Need It. Don't add functionality "just in case."
- **Boy Scout Rule** — Leave the code cleaner than you found it.
- **Fail Fast** — Validate inputs early, surface errors immediately.
- **Least Surprise** — Code should behave as the reader expects.

## SOLID Principles

- **Single Responsibility** — A class/module should have one reason to change
- **Open/Closed** — Open for extension, closed for modification
- **Liskov Substitution** — Subtypes must be substitutable for their base types
- **Interface Segregation** — Prefer small, focused interfaces over large ones
- **Dependency Inversion** — Depend on abstractions, not concretions

## Design Patterns

- Apply design patterns where they solve a real problem — not for their own sake
- Favor composition over inheritance
- Use dependency injection for testability and flexibility
- Prefer immutable data structures when practical
- Use the Strategy pattern for interchangeable behaviors, Observer for event-driven logic, Factory for complex object creation — but only when the pattern genuinely simplifies the code

## Error Handling

- Handle errors properly — no swallowed exceptions
- Use typed/specific errors over generic ones
- Provide meaningful error messages with context
- Clean up resources in error paths (finally, defer, using, etc.)

## Universal Quality Tools

Apply these cross-language tools on every project:

| Tool                      | Purpose                                        | Reference                           |
| ------------------------- | ---------------------------------------------- | ----------------------------------- |
| `.editorconfig`           | Cross-editor indent, charset, EOL consistency  | https://editorconfig.org            |
| `jscpd`                   | Copy-paste detection (all languages)           | https://github.com/kucherenko/jscpd |
| `Semgrep`                 | Multi-language static analysis, custom rules   | https://semgrep.dev                 |
| `SonarQube` / `SonarLint` | Code quality + security dashboard              | https://www.sonarsource.com         |
| `MegaLinter`              | Meta-linter for CI (orchestrates 100+ linters) | https://megalinter.io               |
| `pre-commit`              | Git hook framework for linters/formatters      | https://pre-commit.com              |
| `Trunk`                   | Auto-detect and run linters/formatters         | https://trunk.io                    |
| `Taskfile`                | Task runner for build/test/lint/format         | https://taskfile.dev                |
| `commitlint`              | Commit message convention enforcement          | https://commitlint.js.org           |

- Every project **must** have an `.editorconfig` at the root
- Use `run-quality-checks` to enforce duplicated code checks to catch duplicated code blocks
- Use `run-quality-checks` to enforce linting/formatting before commit
- Use `Taskfile` for consistent `task lint`, `task format`, `task test`, `task validate` commands
