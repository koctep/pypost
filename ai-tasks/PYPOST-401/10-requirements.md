# PYPOST-401: Fix Race Condition in Scheduling Worker

## Overview

**Ticket:** PYPOST-401
**Type:** Debt
**Priority:** High
**Labels:** high-priority, sprint-mar24
**Status:** To Do

**Summary:** Investigate and fix intermittent duplicate executions in the scheduling worker
caused by race conditions.

---

## Context

PyPost is a desktop HTTP client application built on PySide6. HTTP requests are executed
asynchronously via `RequestWorker` (`pypost/core/worker.py`), which extends `QThread`. Each
tab in the UI owns a reference to its current worker (`sender_tab.worker`).

The worker exposes a cooperative stop mechanism via `_is_stopped: bool` and a `stop()` method.
The UI presenter (`tabs_presenter.py`) checks `worker.isRunning()` before creating a new worker
to guard against concurrent executions per tab.

---

## Problem Statement

### Identified Race Conditions

**RC-1: `_is_stopped` reset overwrites a pending stop signal**

`run()` unconditionally resets `self._is_stopped = False` as its first statement. If `stop()`
is called from the main thread between the worker being constructed (or `start()` called) and
`run()` beginning execution on the worker thread, the stop signal is silently discarded. The
request then executes to completion despite the user requesting cancellation.

**RC-2: `_is_stopped` is not thread-safe**

`_is_stopped` is a plain Python `bool`. It is written by `stop()` on the main thread and read
by `check_stop()` on the worker thread without any synchronization primitive (lock,
`threading.Event`, or `QAtomicInt`). While CPython's GIL offers limited protection, this is
not a guaranteed contract and can produce stale reads or torn writes on non-CPython runtimes
or in future Python versions.

**RC-3: Guard window between `isRunning()` check and worker assignment**

In `tabs_presenter.py`, the send-request path checks `sender_tab.worker.isRunning()` to
decide whether to stop the existing worker or create a new one. There is a window between
a worker finishing execution (transitioning `isRunning()` to `False`) and the tab's worker
reference being cleared (`_reset_tab_ui_state` sets `sender_tab.worker = None`). If a rapid
double-click or programmatic trigger fires in this window, two `RequestWorker` instances can
be created and both started, causing duplicate HTTP dispatch and duplicate history recording.

**RC-4: No guard against worker `start()` being called while the thread is finishing**

`QThread.start()` on an already-started thread that has not yet fully terminated is
undefined behaviour. The current code does not guard against this edge case.

---

## Requirements

### REQ-1: Thread-Safe Stop Flag

- **REQ-1.1** Replace the plain `bool` `_is_stopped` with `threading.Event` named `_stop_event`.
- **REQ-1.2** `stop()` must call `_stop_event.set()` instead of assigning a bool.
- **REQ-1.3** `run()` must NOT reset the stop flag at entry. The event must be cleared exactly
  once during worker initialization (`__init__`), so that a `stop()` call arriving before
  `run()` starts is never lost.
- **REQ-1.4** The `check_stop` callback passed to `RequestService.execute()` must delegate to
  `_stop_event.is_set()`.
- **REQ-1.5** No other part of the codebase may write to `_stop_event` except `stop()` and
  `__init__`.

### REQ-2: Prevent Duplicate Execution per Tab

- **REQ-2.1** `tabs_presenter.py` must guarantee that at most one `RequestWorker` is running
  per tab at any time.
- **REQ-2.2** The send-request code path must check whether the current worker exists AND is
  still running before creating a new worker. If a worker exists but `isRunning()` returns
  `False`, the stale reference must be cleaned up before a new worker is created.
- **REQ-2.3** The UI send button must be disabled (or set to "Cancel" state) immediately upon
  starting a worker, and only re-enabled once the worker's `finished` or `error` signal fires.
  This must happen synchronously before `worker.start()` returns to the event loop, preventing
  a second send event from being processed while the first worker is launching.
- **REQ-2.4** A new worker must not be started if `sender_tab.worker` is not `None` and
  `isRunning()` returns `True`; instead the duplicate request must be silently dropped
  (or stop requested, depending on UX intent — see AC-4).

### REQ-3: Worker Lifecycle Hardening

- **REQ-3.1** `RequestWorker.__init__` must initialize `_stop_event` as a cleared
  `threading.Event`.
- **REQ-3.2** Once a worker emits `finished` or `error`, the presenter must set
  `sender_tab.worker = None` before any subsequent send event can be processed.
- **REQ-3.3** `worker.deleteLater()` connections (already present) must be retained so Qt
  cleans up the underlying `QThread` object after signals are processed.

### REQ-4: No New Public Interface Changes

- **REQ-4.1** `RequestWorker.stop()` must remain callable with no arguments.
- **REQ-4.2** `RequestWorker.run()` must retain the same internal logic and signal-emission
  sequence.
- **REQ-4.3** The `check_stop` callable contract (returns `bool`) passed into
  `RequestService.execute()` must be preserved.
- **REQ-4.4** No changes to `RequestService`, `HTTPClient`, or any model class are permitted
  under this ticket.

### REQ-5: Test Coverage

- **REQ-5.1** All existing tests in `tests/test_worker.py` must continue to pass unchanged.
- **REQ-5.2** New unit tests must cover:
  - **REQ-5.2a** `stop()` called before `run()` begins must result in the request being
    cancelled (i.e. `check_stop()` returns `True` from the first poll).
  - **REQ-5.2b** Concurrent `stop()` and `run()` calls do not cause `check_stop()` to
    return `False` after `stop()` was invoked.
  - **REQ-5.2c** A second `send_request_event` fired while a worker `isRunning()` does not
    create a second `RequestWorker` instance (presenter-level test).

---

## Acceptance Criteria

| # | Criterion |
|---|-----------|
| AC-1 | `RequestWorker._stop_event` is a `threading.Event`, not a plain bool. |
| AC-2 | Calling `stop()` before `run()` starts still cancels the request. |
| AC-3 | No lock, busy-wait, or sleep is introduced; only `threading.Event` primitives. |
| AC-4 | At most one `RequestWorker` per tab is running at any given time. |
| AC-5 | Send button is disabled before `worker.start()` is called; re-enabled on finish/error. |
| AC-6 | All existing tests pass without modification. |
| AC-7 | New tests for the race conditions described in REQ-5.2 are present and green. |
| AC-8 | No changes to `RequestService`, `HTTPClient`, or data models. |

---

## Out of Scope

- Retry logic or automatic re-execution on error.
- Cross-tab worker coordination.
- Changes to streaming, metrics, or history recording behaviour.
- Cancellation UI changes beyond disabling/enabling the send button.
- Changes to any layer below `RequestWorker` (i.e. `RequestService` and below).
