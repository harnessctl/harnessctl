---
name: issue-tracking
description: Manage tasks, epics, and bugs based on ISSUE_TRACKING environment variable. Use `env-get` to determine storage (fs or github) and tools.
---

# Issue Tracking

- Run `env-get` tool for the `ISSUE_TRACKING` variable to determine the issue tracking environment and available tools:
  - e.g., `ISSUE_TRACKING=fs,issue-create,issue-list,issue-read` means issues are stored locally in the file system, and you must use those tools to manage them.
  - e.g., `ISSUE_TRACKING=github,gh,cvs_github` means issues are stored on GitHub, and you should use the `gh` cli or `cvs_github` MCP tools.

## Templates

- **Issues:** Follow the instructions in `skills/issue-tracking/issue.md` to format your issue body.
  - _Note:_ The YAML frontmatter (id, type, parent, etc.) is automatically added by the `issue-create` tool (when using `fs`). Do NOT add it yourself when creating an issue. You may update it later if necessary.
- **Comments:** Format your updates and comments using `skills/issue-tracking/comment.md`.

## Content & Format

When describing features, stories, or bugs, use the **Gherkin format** as much as possible for clarity:

```gherkin
As a [persona]
I want to [action]
So that [benefit/value]

# OR

Given [initial context/state]
And [more context]
When [action occurs]
And [more actions]
Then [expected outcome]
And [more outcomes]
```

## Hierarchy & Emoticons

If not created for the file system (`ISSUE_TRACKING=fs,...`), the issue title **MUST** contain as prefix the exact emoticon (e.g., `🚀 Q3 Goals`). Do **NOT** manage or use labels.

- **🚀 Initiative** (`initiative`): Top-level business goal.
  - **🏔️ Epic** (`epic`): Large project phase.
    - **📖 Story** (`story`): User-facing feature.
      - **🛠️ Task** (`task`): Atomic implementation step.
      - **🐛 Bug** (`bug`): Defect in a story.
    - **🐛 Bug** (`bug`): Defect in an epic.

## Issue Rules

- **Links over Text:** Link to local `.specs/` files in comments instead of pasting large content.
- **Hierarchy Links:** Use markdown (`#42`) to link parent/child and dependent issues.
- **Report Failures:** Always post execution failures as CVS comments so humans can see them.
