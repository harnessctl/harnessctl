---
name: lang-tsx
description: React and TSX development standards and tooling.
---

# TSX Standards

- **Tooling:** `Prettier`, `eslint-plugin-react`, `typescript-eslint`.
- **Components:** Functional components only. No `React.FC` or `React.FunctionComponent`.
- **Props:** Type your props explicitly using `interface` or `type`.
- **Hooks:** Type hooks explicitly when inference is insufficient (e.g., `useState<User | null>(null)`).
- **Architecture:** Composition over prop drilling. Collocate components with their styles and tests.

Always load `clean-code` alongside this skill.
