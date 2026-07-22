# PYPOST-872: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Decision **ENABLE**: `test` / `test-slow` / `test-agent-e2e` now depend on
`venv-test` (+ existing `venv-otel`), matching `test-cov`. Contract tests and
dev docs updated. Items below are non-blocking. **Do not create Jira tickets
in this step** — list unticketed follow-ups for the orchestrator.

## Shortcuts Taken

- **No stamp/caching for `venv-test` / `venv-otel`.** Every Make visit still
  re-runs `pip install -e ".[dev]"` then `".[otel]"`. Accepted because
  `venv-otel` already had that cost; `make install` remains the preferred
  one-shot path.
- **`lint` / `run` left marker-only.** Ticket title scoped pytest targets;
  flake8 still needs `[dev]` via explicit `venv-test` / `install`.
- **Did not switch pytest targets to depend on `install` alone.** Kept
  split extras to mirror `test-cov` and minimize recipe churn.
- **Full `make check` / full suite not re-run.** Validated
  `tests/test_makefile.py` (39 passed) + `make lint`.

## Code Quality Issues

- None that block close. Optional: order-only prerequisites or stamp files
  for install extras (see follow-ups).

## Missing Tests

| Scenario | Status |
| --- | --- |
| `venv-test` in `test` / `test-agent-e2e` / `test-slow` prereqs | Covered |
| Bare venv `make test` succeeds via auto `venv-test` | Covered |
| `run` / `lint` still exclude `venv-test` | Covered |
| Stamp/idempotent skip when extras already installed | Not covered — follow-up |
| Full `make check` after this story | Not re-run — NON-BLOCKER |

Timeout markers: module `pytestmark` on `test_makefile.py`. **No timeout-marker
blockers.**

## Performance Concerns

- Dual editable pip on each `make test` / `test-agent-e2e` can add seconds
  locally even when packages are already satisfied. Prefer `make install`
  once; consider stamp files if the cost becomes painful in agent loops.

## Follow-Up Tasks

1. **Stamp / cache `venv-test` and `venv-otel` installs**
   - Priority: Low
   - Touch files under `.venv/` so Make skips pip when extras are current;
     reduce repeated editable install cost on every test target.
   - Jira: [PYPOST-905](https://pypost.atlassian.net/browse/PYPOST-905)

2. **Optional: `lint` depend on `venv-test`**
   - Priority: Lowest
   - Same DX argument as pytest targets; out of PYPOST-872 title scope.
   - Jira: [PYPOST-906](https://pypost.atlassian.net/browse/PYPOST-906)

## Blocker Verdict

**SAFE TO CLOSE** — acceptance criteria met; no blockers relative to DoD.
