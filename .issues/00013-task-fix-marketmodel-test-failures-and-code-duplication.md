---
id: "00013"
type: task
title: "Fix MarketModel test failures and code duplication"
status: in_progress
parent: "00012"
opencode-agent: lead-engineer
opencode-assignee: lead-engineer
---

# Fix MarketModel test failures and code duplication

Given the recent introduction of `intelligence_source` in `MarketModel`
When running tests
Then `test_market_merge` fails due to missing arguments.

Also, there is significant code duplication between `harnessctl/commands/models.py` and `harnessctl/commands/recommend.py` regarding filters.

## Tasks

- [ ] Fix `tests/pricing/test_pricing.py` by adding `intelligence_source` to `MarketModel` calls.
- [ ] Refactor filters into a shared utility or base class.
- [ ] Verify all tests pass.

## Comments
