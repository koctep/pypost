# PYPOST-401: Observability

## Scope

This document covers the logging additions made during the observability pass for PYPOST-401
(Fix Race Condition in Scheduling Worker). Only code paths introduced or modified by this task
were in scope; pre-existing logging was left untouched.

---

## Gaps Identified

| Location | Gap |
|---|---|
| `worker.py::stop()` | No record that a stop was requested — essential for correlating cancellation events with race-condition investigations |
| `worker.py::run()` | No lifecycle boundary logs — impossible to tell from logs when a thread started or whether it completed normally vs. was stopped |
| `tabs_presenter.py::_handle_send_request` | New stale-worker cleanup path (PYPOST-401 RC-3 fix) was completely silent |

---

## Changes Made

### `pypost/core/worker.py`

#### `stop()` — debug log on stop request

```python
logger.debug(
    "worker_stop_requested method=%s url=%s",
    self.request_data.method, self.request_data.url,
)
```

**Why:** Allows operators to confirm that `stop()` was called and correlate it with any
subsequent `worker_run_completed stopped=True` entry, proving the `threading.Event` path
through the fix fired correctly.

#### `run()` — debug log at thread start

```python
logger.debug(
    "worker_run_started method=%s url=%s request_id=%s",
    self.request_data.method, self.request_data.url, self.request_data.id,
)
```

**Why:** Establishes the thread boundary in the log stream. When investigating whether a
second worker was spuriously created (RC-3/RC-4), two `worker_run_started` entries for the
same `request_id` would be definitive proof.

#### `run()` — debug log at normal completion

```python
stopped = self._stop_event.is_set()
logger.debug(
    "worker_run_completed method=%s url=%s stopped=%s",
    self.request_data.method, self.request_data.url, stopped,
)
```

**Why:** `stopped=True` confirms the cancellation path executed end-to-end. `stopped=False`
confirms a normal finish. Together with the `worker_run_started` entry, these bracket the
full worker lifetime.

---

### `pypost/ui/presenters/tabs_presenter.py`

#### `_handle_send_request` — debug log on stale-worker cleanup

```python
logger.debug(
    "stale_worker_cleared method=%s url=%s",
    request_data.method, request_data.url,
)
```

**Why:** The stale-reference cleanup block is the new code path added to fix RC-3. Without
a log here it is impossible to observe in production whether the cleanup is firing as
expected (e.g. because `_reset_tab_ui_state` Qt-dispatch was delayed) or is never firing
(which would indicate the guard is not needed in practice).

---

## Log Level Rationale

All additions use `DEBUG`. The existing codebase already uses `INFO` for user-visible
lifecycle events (`request_send_initiated`, `request_finished`, `request_stop_requested`)
and `ERROR`/`WARNING` for failures. The new entries describe internal thread mechanics that
are only useful during debugging and should not appear in production INFO-level output.

---

## No Metrics Changes

The race-condition fix has no new user-facing behaviour that warrants a new metric counter.
The existing `track_request_sent` and `track_response_received` metrics already capture the
start and end of each request lifecycle. No new `MetricsManager` instrumentation was added.

---

## Files Changed

| File | Change |
|---|---|
| `pypost/core/worker.py` | 3 `logger.debug` calls added in `stop()` and `run()` |
| `pypost/ui/presenters/tabs_presenter.py` | 1 `logger.debug` call added in stale-cleanup block |
