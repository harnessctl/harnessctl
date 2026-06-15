---
id: "00020"
type: task
title: "Implement Taxonomy Client in harnessctl"
status: done
parent: "00018"
depends: "00019"
author: lead-engineer
assignee: lead-engineer
created: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
---

# Implement Taxonomy Client in harnessctl

As a user
I want `harnessctl` to download the taxonomy DB
So that my intents are properly classified.

- [x] Add msgpack and zstandard dependencies
- [x] Implement `TaxonomyClient.fetch()`
- [x] Implement `get_intent_complexity` algorithm
- [x] Write tests using `respx`

## Comments

Done.
