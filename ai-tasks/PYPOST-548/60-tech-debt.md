# PYPOST-548: Technical Debt Analysis

## Shortcuts Taken

None for the production fix — reordering `_on_request_persisted` is the minimal correct fix.

Marker rollout used a one-off script to add `pytestmark` to 77 files; tiers were assigned by
filename heuristics (30/60/120s). Individual tests that need tighter or looser bounds can
override at class or function level later.

## Code Quality Issues

- **E402 in test files**: `pytestmark` sits after `import pytest` but before other imports in
  many files, matching the documented pattern in `do-testing.md`. Acceptable for pytest
  module marks; optional follow-up could move marks below all imports with `# noqa: E402` if
  flake8 is extended to `tests/`.

- **Pre-existing `make lint` failures** in unrelated `pypost/` files (see
  `40-code-cleanup.md`).

## Missing Tests

- No dedicated unit test for `_on_request_persisted` ordering in isolation; covered indirectly
  by `test_save_overwrite_updates_all_matching_tab_labels` and sibling-reload tests in
  `test_tabs_presenter.py`.

## Performance Concerns

None. Per-test signal timeouts add negligible overhead; full suite completes in ~7s.

## Follow-up Tasks

| Item | Priority | Notes |
| ---- | -------- | ----- |
| Extend `make lint` to `tests/` with E402 noqa policy | Low | Optional consistency |
| Per-test timeout overrides for slow outliers | Low | Only if CI reports timeouts |
| Fix pre-existing E501/E203 in unrelated pypost files | Low | Out of PYPOST-548 scope | [PYPOST-651](https://pypost.atlassian.net/browse/PYPOST-651) |

## Blocker Review

**Verdict: SAFE TO CLOSE**

- Layer 1 hang fixed; regression test hardened against modal reintroduction.
- Layer 2 timeout policy enforced; docs match implementation.
- `make test` completes with 886 passed.
- No blockers.
