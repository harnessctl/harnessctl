# Issue Writing Instructions

When creating or updating an issue, structure the body of the issue as follows:

## YAML Frontmatter Reference (For Local `fs` tracking)

_Note: The YAML frontmatter is automatically injected by the `issue-create` tool at the top of the file when creating a new issue. You do not need to generate it initially, but you MUST use this reference to update the fields (like `status`, `depends`, or `parent`) using the `edit` tool as the issue progresses._

```yaml
id: "00001" # 5-digit zero-padded / only if ISSUE_TRACKING contains 'fs'
type: <type> # initiative | epic | story | task | bug
parent: <parent-issue> # Optional: ID of the parent issue
depends: [] # Optional: Array of blocking issue IDs
opencode-agent: <agent-name>
status: open # open | in_progress | done | closed / only if ISSUE_TRACKING contains 'fs'
author: name # Optional: Author name
```

---

## Issue Body Structure

1. **Title**: A clear and concise title. (If not using local `fs`, include the hierarchy emoticon in the title).

2. **Description**: Use the Gherkin format to clearly state the user story or scenario:

   ```gherkin
   As a [persona]
   I want to [action]
   So that [benefit/value]

   # OR

   Given [initial context/state]
   When [action occurs]
   Then [expected outcome]
   ```

3. **Details (Based on Type)**:
   - **Initiative/Epic/Story:** Include Scope, Goals, Non-Goals, and Risks.
   - **Task:** Include a detailed Description and Technical Requirements.
   - **Bug:** Include Steps to Reproduce, Expected Behavior, and Actual Behavior.

4. **Acceptance Criteria**:
   - Provide a list of clear, testable criteria that must be met for the issue to be considered done.

5. **Optional Sections**:
   - **Open Questions:** Any unresolved questions that need answers.
   - **Risks:** Potential risks and mitigations (e.g., `- <Risk> — <Mitigation>`).
