---
id: "00012"
type: epic
title: "Implement Unified Model Discovery and Recommendation Engine"
status: in_progress
opencode-agent: lead-engineer
opencode-assignee: lead-engineer
---

# Implement Unified Model Discovery and Recommendation Engine

As a user
I want to have a unified way to list and discover models across multiple providers (local and remote)
So that I can get hardware-aware recommendations based on intelligence, speed, and cost.

## Tasks

- [x] Implement intelligence normalization (0-100) for Artificial Analysis and ELO scores.
- [x] Add intelligence source indicators (★, ○, ≈) to the model list.
- [x] Implement hardware-aware filtering (VRAM/RAM) for local models.
- [x] Add min/max filters for intelligence, speed, price, and context window.
- [x] Update recommendation engine with logarithmic scoring for context and price.
- [x] Add GitHub and Copilot model discovery support.
- [ ] Fix failing tests in `tests/pricing/test_pricing.py`.
- [ ] Refactor repetitive code in `models.py` and `recommend.py`.

## Acceptance Criteria

- `harnessctl models list` shows unified metrics across all providers.
- `harnessctl recommend` provides hardware-safe suggestions.
- All tests pass (including `test_market_merge`).
- No static overrides for provider discovery.

## Comments
