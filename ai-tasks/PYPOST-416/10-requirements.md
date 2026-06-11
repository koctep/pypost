# PYPOST-416 — Requirements: Stale Worker Cleared Log Test

> Analyst: 2026-06-11
> Jira: PYPOST-416
> Parent: PYPOST-401 (TD-2)
> Type: Debt
> Priority: Low

---

## 1. Problem Statement

PYPOST-415 added `test_stale_worker_cleared_allows_new_worker`, which verifies that a finished
but stale `tab.worker` reference is cleared and a new `RequestWorker` is created. It does not
assert the RC-3 observable debug log `stale_worker_cleared` emitted by
`_clear_tab_worker(..., reason="stale")`.

---

## 2. Scope

### In-Scope

1. Verify existing behavioral test from PYPOST-415 remains sufficient for creation path.
2. Add a focused unit test asserting the `stale_worker_cleared` DEBUG log with method and URL.
3. All existing worker race tests must pass.

### Out-of-Scope

- Production code changes (log already exists in `_clear_tab_worker`).
- Broader observability refactors.

---

## 3. Functional Requirements

### FR-1 — Log assertion on stale path

When `_handle_send_request` detects a non-running stale worker and clears it, the test must
capture and assert a DEBUG log record containing `stale_worker_cleared`, the request method,
and URL.

### FR-2 — Behavioral coverage retained

`test_stale_worker_cleared_allows_new_worker` continues to cover worker creation after stale
clearance without modification.

---

## 4. Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-1 | New test passes with `assertLogs` at DEBUG on `pypost.ui.presenters.tabs_presenter`. |
| AC-2 | Log message includes `stale_worker_cleared`, `method=GET`, and `url=http://x`. |
| AC-3 | All tests in `tests/test_worker_race.py` pass. |
| AC-4 | No production code changes required. |
