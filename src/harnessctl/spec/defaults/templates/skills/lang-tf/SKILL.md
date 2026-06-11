---
name: lang-tf
description: Terraform / OpenTofu standards and tooling.
---

# TF Standards

- **Style:** [HashiCorp Style Guide](https://developer.hashicorp.com/terraform/language/style).
- **Tooling:** `terraform fmt` / `tofu fmt`, `tflint`, `tfsec` / `checkov`.
- **Structure:** One concern per file (`main.tf`, `variables.tf`, `outputs.tf`).
- **Best Practices:** Use Modules for reusable components. Pin provider versions. Use `validation` blocks on variables.
- **State:** Use remote state backends with state locking. Never commit `.tfstate`.

Always load `clean-code` alongside this skill.
