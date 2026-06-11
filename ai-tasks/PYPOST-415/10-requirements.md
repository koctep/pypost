# PYPOST-415 — Requirements: Worker Reference Cleanup via Qt Signals

> Analyst: 2026-06-11
> Jira: PYPOST-415
> Parent: PYPOST-401 (TD-1)
> Type: Debt
> Priority: Medium

---

## 1. Problem Statement

`TabsPresenter._reset_tab_ui_state` previously cleared `tab.worker = None` alongside UI
button reset. That method is invoked from `finished` and `error` signal handlers, which are
queued on the Qt event loop. Between a worker thread finishing (`isRunning()` → `False`) and
the handler running, `tab.worker` still pointed at the dead thread.

PYPOST-401 added a stale-reference guard in `_handle_send_request` to cover that window, but
two unrelated code paths then maintained the same invariant, with worker lifecycle hidden
inside a UI-reset helper.

---

## 2. Scope

### In-Scope

1. Separate worker lifecycle from UI reset: `_reset_tab_ui_state` must only restore the Send
   button.
2. Introduce a single `_clear_tab_worker` helper as the authority for releasing `tab.worker`.
3. Call `_clear_tab_worker` from completion handlers and the existing stale guard.
4. Document the Qt queued-signal gap and why the stale guard remains.
5. Add a test covering the stale-worker path (RC-3 observable path).
6. All existing tests must pass.

### Out-of-Scope

- Changing `RequestWorker` signal semantics.
- Removing the stale guard (still required until Qt delivers completion handlers).
- PYPOST-416 (dedicated stale-path log assertion test beyond creation path).

---

## 3. Functional Requirements

### FR-1 — Single cleanup authority

Only `_clear_tab_worker` may set `tab.worker = None`.

### FR-2 — UI reset isolation

`_reset_tab_ui_state` re-enables the Send button and restores its label only.

### FR-3 — Completion handlers clear worker first

`_on_request_finished` and `_on_request_error` call `_clear_tab_worker` before UI reset.

### FR-4 — Stale guard uses shared helper

The RC-3 stale guard in `_handle_send_request` delegates to `_clear_tab_worker` with
`reason="stale"` so logging stays in one place.

### FR-5 — Test coverage

A new test proves that a finished-but-stale `tab.worker` reference allows a new
`RequestWorker` to be created.

---

## 4. Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-1 | `_reset_tab_ui_state` does not reference `tab.worker`. |
| AC-2 | `_clear_tab_worker` exists and is the sole writer of `tab.worker = None`. |
| AC-3 | Completion handlers call `_clear_tab_worker` before UI reset. |
| AC-4 | Stale guard in `_handle_send_request` uses `_clear_tab_worker`. |
| AC-5 | `test_stale_worker_cleared_allows_new_worker` passes. |
| AC-6 | All existing worker race tests pass. |

---

## 5. Key Files

| File | Relevance |
|------|-----------|
| `pypost/ui/presenters/tabs_presenter.py` | Primary change |
| `tests/test_worker_race.py` | New stale-path test |
| `doc/dev/request_execution.md` | Worker lifecycle documentation |
