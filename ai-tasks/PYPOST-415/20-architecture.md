# PYPOST-415 — Architecture: Consolidate Tab Worker Cleanup

> Senior Engineer: 2026-06-11
> Jira: PYPOST-415
> Status: Approved

---

## 1. Overview

Separate worker reference lifecycle from UI state reset. One helper owns `tab.worker = None`;
completion handlers and the stale guard both call it.

---

## 2. Before / After

### Before

```
RequestWorker.finished/error (queued)
  → _on_request_finished / _on_request_error
      → _reset_tab_ui_state
            send_btn restore
            tab.worker = None        ← mixed concern

_handle_send_request (stale guard)
  → inline tab.worker = None         ← duplicate path
```

### After

```
RequestWorker.finished/error (queued)
  → _on_request_finished / _on_request_error
      → _clear_tab_worker(tab)       ← worker lifecycle
      → _reset_tab_ui_state(tab)     ← UI only

_handle_send_request (stale guard)
  → _clear_tab_worker(tab, reason="stale", request_data=...)
```

---

## 3. `_clear_tab_worker` Design

```python
def _clear_tab_worker(
    self,
    tab: RequestTab,
    *,
    reason: str = "completed",
    request_data: RequestData | None = None,
) -> None:
```

| Parameter | Purpose |
|-----------|---------|
| `reason="completed"` | Normal completion/error handler path; no extra log |
| `reason="stale"` | RC-3 guard; emits existing `stale_worker_cleared` debug log |

Early return when `tab.worker is None` keeps calls idempotent.

---

## 4. Why the Stale Guard Stays

Qt delivers `finished`/`error` to the main thread asynchronously. After `run()` returns,
`isRunning()` is `False` but the handler may not have run yet. The stale guard in
`_handle_send_request` closes that window when the user sends again before the event loop
dispatches the completion handler.

---

## 5. Test Plan

| Test | Assertion |
|------|-----------|
| `test_stale_worker_cleared_allows_new_worker` | `isRunning() == False` stale ref → new `RequestWorker` created and started |
| Existing `test_worker_race.py` cases | Unchanged behavior for stop flag and active-worker guard |

---

## 6. File Change Summary

| File | Change |
|------|--------|
| `tabs_presenter.py` | Add `_clear_tab_worker`; update 3 call sites; trim `_reset_tab_ui_state` |
| `tests/test_worker_race.py` | +1 test |
| `doc/dev/request_execution.md` | Tab worker lifecycle section |

Estimated delta: ~45 lines.
