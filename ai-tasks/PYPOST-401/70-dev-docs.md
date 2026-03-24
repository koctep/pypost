# PYPOST-401: Developer Documentation

## What Changed and Why

PYPOST-401 fixed four race conditions in the HTTP request worker lifecycle that could cause
duplicate request execution, silent cancellation failures, or undefined behaviour when requests
were started or stopped in rapid succession.

---

## Background: Request Worker Lifecycle

Each tab in PyPost owns a single `RequestWorker` instance at a time, stored in `sender_tab.worker`.
The worker is a `QThread` subclass that calls `RequestService.execute()` on a background thread
and emits Qt signals (`chunk_received`, `headers_received`, `finished`, `error`) back to the
main thread.

The UI presenter (`TabsPresenter`) drives the lifecycle:

```
User clicks Send
  → _handle_send_request()
      → construct RequestWorker
      → sender_tab.worker = worker   ← assigned BEFORE start (PYPOST-401 fix)
      → worker.start()
          → (worker thread) run()
              → service.execute(stop_flag=check_stop, ...)
              → emit finished / error
  → _reset_tab_ui_state()
      → sender_tab.worker = None
      → re-enable send button
```

---

## Changes

### `pypost/core/worker.py`

#### `_stop_event` replaces `_is_stopped`

| Before | After |
|--------|-------|
| `self._is_stopped = False` (plain bool) | `self._stop_event = threading.Event()` |
| `stop()` sets `self._is_stopped = True` | `stop()` calls `self._stop_event.set()` |
| `run()` reset `self._is_stopped = False` at entry | `run()` does **not** touch `_stop_event` |
| `check_stop()` returned `self._is_stopped` | `check_stop()` returns `self._stop_event.is_set()` |

**Why this matters:**

- The old `run()` reset overwrote any `stop()` call that arrived before the thread started
  executing (RC-1).
- A plain `bool` has no synchronisation guarantees across threads (RC-2). `threading.Event`
  provides an internal lock and is safe to read/write from different threads.

**Invariant:** `_stop_event` is cleared exactly once — in `__init__`. It is set only by `stop()`.
Nothing else touches it. A stopped worker cannot be restarted; construct a new instance.

#### Logging additions

Three `logger.debug` calls were added:

| Location | Key | Purpose |
|----------|-----|---------|
| `stop()` | `worker_stop_requested` | Confirms cancellation was requested; correlates with `stopped=True` at completion |
| `run()` entry | `worker_run_started` | Marks thread boundary; duplicate entries for the same `request_id` indicate RC-3/RC-4 regression |
| `run()` before `finished` | `worker_run_completed stopped=<bool>` | Confirms whether the request completed normally or was cancelled |

---

### `pypost/ui/presenters/tabs_presenter.py` — `_handle_send_request`

Two changes were made to the guard logic at the start of this method:

#### 1. Stale reference cleanup (RC-3 fix)

```python
if sender_tab.worker is not None and not sender_tab.worker.isRunning():
    logger.debug("stale_worker_cleared method=%s url=%s", ...)
    sender_tab.worker = None
```

Added immediately before the active-worker guard. This handles the window between a worker
finishing (`isRunning()` → `False`) and `_reset_tab_ui_state` being dispatched through the Qt
event loop. Without this cleanup, a second send event arriving in that window would bypass the
active-worker guard and create a duplicate worker.

#### 2. Assignment before `start()` (RC-4 fix)

```python
# Before PYPOST-401
worker.start()
sender_tab.worker = worker

# After PYPOST-401
sender_tab.worker = worker
worker.start()
```

`sender_tab.worker` is now set before the thread is started. This closes the window where the
thread could finish and `_reset_tab_ui_state` could fire before `sender_tab.worker` was
populated, leaving the reference `None` instead of pointing to the worker.

#### Guard expression tightened

`if sender_tab.worker and ...` was changed to `if sender_tab.worker is not None and ...` to
make the null check explicit and avoid accidental falsy matches.

---

## New Tests — `tests/test_worker_race.py`

| Test | Requirement | What it verifies |
|------|-------------|-----------------|
| `test_stop_before_run_check_stop_is_true` | REQ-5.2a | `stop()` before `run()` makes `check_stop()` return `True` immediately |
| `test_stop_flag_not_overwritten_after_stop` | REQ-5.2b | `run()` does not reset the stop flag set by a prior `stop()` call |
| `test_second_send_while_running_does_not_create_second_worker` | REQ-5.2c | A second send event while a worker is running does not construct a new `RequestWorker` |

All three tests call `worker.run()` directly (not via `QThread.start()`) to keep them
synchronous and free of real threading. `worker.service.execute` is patched in all cases.

---

## Debugging Race Conditions with the New Logs

Enable `DEBUG` log level (`--log-level DEBUG` or `PYPOST_LOG_LEVEL=DEBUG`) and look for these
sequences:

**Normal request flow:**
```
worker_run_started method=GET url=https://...  request_id=abc
worker_run_completed method=GET url=https://...  stopped=False
```

**User-cancelled request:**
```
worker_stop_requested method=GET url=https://...
worker_run_completed method=GET url=https://...  stopped=True
```

**Stale worker cleared (RC-3 path firing):**
```
stale_worker_cleared method=GET url=https://...
```
This means a worker finished but the Qt `_reset_tab_ui_state` dispatch had not yet run when
the next send event arrived. Normal, but worth noting if it appears frequently.

**Regression indicator — duplicate worker creation:**
```
worker_run_started method=GET url=https://...  request_id=abc
worker_run_started method=GET url=https://...  request_id=abc   ← same id, second start
```
Two `worker_run_started` entries with the same `request_id` indicate RC-3 or RC-4 has
regressed and two workers were created for the same request.

---

## Files Changed

| File | Role |
|------|------|
| `pypost/core/worker.py` | Thread-safe stop flag + lifecycle logging |
| `pypost/ui/presenters/tabs_presenter.py` | Stale cleanup + assignment ordering fix |
| `tests/test_worker_race.py` | New; three race-condition regression tests |
