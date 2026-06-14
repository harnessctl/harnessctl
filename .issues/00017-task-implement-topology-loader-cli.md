---
id: "00017"
type: task
title: "Implement Topology Loader and CLI Command"
status: open
parent: "00014"
depends: "00016"
author: lead-engineer
assignee: lead-engineer
created: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
---

# Implement Topology Loader and CLI Command

As a user
I want to run `harnessctl topology create <name> --config my-team.jsonnet`
So that my topology is evaluated, skills are discovered, and the final harness configuration is exported.

- Create `src/harnessctl/topology/loader.py`
- Add `topology create` command to CLI
- Wire Jsonnet evaluation and Discovery Engine together

## Comments
