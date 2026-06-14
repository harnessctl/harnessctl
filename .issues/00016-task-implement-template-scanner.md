---
id: "00016"
type: task
title: "Implement Template Scanner and Discovery Engine"
status: open
parent: "00014"
depends: "00015"
author: lead-engineer
assignee: lead-engineer
created: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
---

# Implement Template Scanner and Discovery Engine

As a developer
I want a discovery engine to parse Markdown templates for `{% load_skill skills="..." %}` tags
So that the system can automatically provision required skills for the agents in the topology.

- Create `src/harnessctl/discovery/scanner.py` and `engine.py`
- Implement regex/Jinja parsing for the tag
- Cross-reference found skills with local skill directories

## Comments
