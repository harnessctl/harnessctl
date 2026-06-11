---
name: developer-devops
description: DevOps and infrastructure standards — principles for IaC, CI/CD, and automation. Load when writing infrastructure or automation code.
---

# DevOps & Infrastructure Standards

Always load `clean-code` alongside this skill.
Use the `detect-language` tool to dynamically load the language-specific skill (e.g. `lang-tf`, `lang-sh`, `lang-yaml`) for the automation code you are writing.
Run the `env-get` tool for the `DEVELOPER_SKILLS` variable. If it returns a comma-separated list of skill names, load each of them.

## Cross-Cutting Rules

- **Idempotency**: Every operation safe to run multiple times with the same result. Test by running twice.
- **Immutable infra**: Replace over mutate. Build images (Docker, AMI) rather than patch in place.
- **Secrets**: Never in VCS. Vault solutions (HashiCorp Vault, AWS SM, SOPS). Inject at runtime via env or mounted secrets.
- **Least privilege**: Minimal IAM/RBAC. Separate service accounts per workload. No wildcard permissions in production.
- **Drift detection**: `plan` in CI on schedule. Alert on unexpected changes.
- **State**: Remote with locking (S3+DynamoDB, GCS, Azure Blob). Never commit state files. Workspaces or directories per environment.
- **CI/CD pipeline**: Lint → format check → plan → approval gate → apply. Never auto-apply to production. Pin tool versions.
- **Monitoring**: Define alerts alongside resources as code. Structured logging for automation.
- **Docs**: Every module/role gets a README (inputs, outputs, usage). `terraform-docs` in CI.
- **Automation**: Use `run-quality-checks` to run validations, formatters, and tests before finalizing.

## Ansible Rules

**Ansible** — Roles for reusable units. `ansible-vault` for secrets. Fully qualified collection names (`ansible.builtin.copy`). `block`/`rescue`/`always` for error handling. Tags for selective runs. Per-environment inventory. `--check` before apply.
