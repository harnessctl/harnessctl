---
id: "00019"
type: task
title: "Deploy Harness Taxonomy to GitHub Releases"
status: done
parent: "00018"
author: lead-engineer
assignee: lead-engineer
created: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
---

# Deploy Harness Taxonomy to GitHub Releases

As a maintainer
I want the harness-taxonomy repository to automatically package and release the DB on every push to main
So that `harnessctl` clients can download the latest version.

- [x] Create `./harness-taxonomy` dir
- [x] Write `taxonomy.json`
- [x] Write `build.py` using msgpack and zstandard
- [x] Create `.github/workflows/release.yml`

## Comments

Done.
