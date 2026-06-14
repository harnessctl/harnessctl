---
id: "00015"
type: task
title: "Implement Jsonnet Integration and Hardware Binding"
status: open
parent: "00014"
author: lead-engineer
assignee: lead-engineer
created: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
---

# Implement Jsonnet Integration and Hardware Binding

As a user
I want to use Jsonnet to define my agent topology and have sysprobe hardware details available in the configuration
So that my multi-agent setups can be conditionally logic-driven based on my local hardware constraints.

- Create `src/harnessctl/topology/jsonnet.py`
- Implement wrapper around `go-jsonnet` or `python-jsonnet`
- Inject `sysprobe` details into the evaluation context

## Comments
