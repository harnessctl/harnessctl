---
name: developer-backend
description: Backend development standards — general backend architecture, security, and tooling. Load when writing backend code.
---

# Backend Development Standards

Always load `clean-code` alongside this skill.
Use the `detect-language` tool to dynamically load the language-specific skill (e.g. `lang-py`, `lang-go`) for the code you are writing.
Run the `env-get` tool for the `DEVELOPER_SKILLS` variable. If it returns a comma-separated list of skill names, load each of them.

## Cross-Cutting Rules

- **Errors**: Return explicitly. Never swallow, never throw for control flow. Include context (what failed, with what input).
- **DI**: Accept interfaces, return concretes. Wire at entry point.
- **Logging**: Structured (JSON). Correlation/request IDs. Never log secrets.
- **Security**: Secrets from env or secret manager — never VCS. Parameterized queries. Validate inputs. Timeouts on HTTP clients.
- **Config**: Env vars with safe defaults. Validate at startup, fail fast.
- **Testing**: Test error paths. Table-driven/parameterized. Testcontainers for integration.
- **Automation**: Use `run-quality-checks` to run validations, formatters, and tests before finalizing.
