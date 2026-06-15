---
id: "00018"
type: epic
title: "Implement Harness Taxonomy Registry (The Brain)"
status: done
author: lead-engineer
assignee: lead-engineer
created: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
---

# Implement Harness Taxonomy Registry (The Brain)

As a user
I want a standalone taxonomy registry deployed as a GitHub release
So that harnessctl can download the latest semantic knowledge base to evaluate intent complexity.

- Create `./harness-taxonomy` project.
- Implement JSON schema and build script (msgpack + zstd).
- Create GitHub Actions release workflow.
- Update `harnessctl` to download and read the taxonomy.

## Comments
