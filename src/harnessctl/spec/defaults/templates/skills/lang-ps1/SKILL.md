---
name: lang-ps1
description: PowerShell development standards and tooling.
---

# PS1 Standards

- **Style:** [PowerShell Practice and Style](https://poshcode.gitbook.io/powershell-practice-and-style).
- **Tooling:** `PSScriptAnalyzer`, `Pester`.
- **Idioms:** Use approved verbs (`Get-`, `Set-`, `New-`). Output objects, not strings (pipeline-friendly).
- **Safety:** Use `[CmdletBinding()]` on advanced functions. Use `-ErrorAction Stop` to catch errors in `try/catch`.
- **Dependencies:** Use `#Requires` to enforce prerequisites.

Always load `clean-code` alongside this skill.
