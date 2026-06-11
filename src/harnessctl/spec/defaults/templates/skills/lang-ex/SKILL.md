---
name: lang-ex
description: Elixir development standards and tooling.
---

# EX Standards

- **Style:** [Elixir Style Guide](https://github.com/christopheradams/elixir_style_guide).
- **Tooling:** `mix format`, `Credo`, `Dialyxir`, `ExUnit`.
- **Idioms:** Leverage the pipe operator (`|>`). Use pattern matching in function heads.
- **Errors:** Return `{:ok, value}` or `{:error, reason}` tuples.
- **Architecture:** "Let it crash" — rely on OTP Supervisors and supervision trees for fault tolerance.

Always load `clean-code` alongside this skill.
