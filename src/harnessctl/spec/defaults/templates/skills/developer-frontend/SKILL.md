---
name: developer-frontend
description: Frontend development standards — UI/UX principles, accessibility, state management, and component patterns. Load when writing frontend code.
---

# Frontend Development Standards

Always load `clean-code` alongside this skill.
Use the `detect-language` tool to dynamically load the language-specific skill (e.g. `lang-ts`, `lang-vue`, `lang-css`) for the frontend code you are writing.
Run the `env-get` tool for the `DEVELOPER_SKILLS` variable. If it returns a comma-separated list of skill names, load each of them.

## Cross-Cutting Rules

- **Accessibility**: WCAG 2.1 AA minimum. Semantic HTML. ARIA only when native elements insufficient. Keyboard navigable. Contrast ≥ 4.5:1. Test with axe-core / Lighthouse.
- **Performance**: Lazy-load routes and heavy components. Code-split at route boundaries. Optimize images (WebP, lazy). Bundle size budgets. Avoid layout shifts (CLS).
- **State**: Local first. Lift only when shared. Framework-native before external libraries. Normalize complex state.
- **Components**: Single responsibility. Props in, events/callbacks out. No direct DOM manipulation. Presentational components are pure functions of props.
- **Testing pyramid**: Unit for logic/utilities. Component for rendering/interaction. e2e for critical flows only.
- **Build**: Vite for new projects. Use `run-quality-checks` to run validations, formatters, and tests before finalizing.
- **Security**: Sanitize user content. Never `innerHTML`/`v-html`/`dangerouslySetInnerHTML` with untrusted data. CSP headers. HTTPS only.

## Frameworks (Angular)

**Angular** — Feature modules. Smart vs presentational components. OnPush change detection. Reactive forms. `takeUntilDestroyed` or `async` pipe for RxJS. Standalone components (17+).
