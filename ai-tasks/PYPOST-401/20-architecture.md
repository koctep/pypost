# PYPOST-401: Architecture — Fix Race Condition in Scheduling Worker

## Overview

Two files require changes: `pypost/core/worker.py` and `pypost/ui/presenters/tabs_presenter.py`.
One new test file is added: `tests/test_worker_race.py`.
Existing test files are left untouched.

---

## 1. Race Condition Analysis

### RC-1 & RC-2: `_is_stopped` in `worker.py`

| Location | Current code | Problem |
|---|---|---|
| `__init__` | `self._is_stopped = False` | Plain bool, no synchronisation primitive |
| `run()` line 46 | `self._is_stopped = False` | Overwrites any `stop()` call that arrived before `run()` began |
| `stop()` | `self._is_stopped = True` | Unsynchronised write from main thread |
| `check_stop()` | `return self._is_stopped` | Unsynchronised read on worker thread |

### RC-3 & RC-4: Worker assignment order in `tabs_presenter.py`

| Location | Current code | Problem |
|---|---|---|
| `_handle_send_request` line 361 | `worker.start()` then `sender_tab.worker = worker` | Window between start and assignment allows duplicate worker creation |
| Guard (line 315) | Only checks `worker.isRunning()` | Stale (finished but not yet cleared) worker reference passes the guard |

---

## 2. Solution Design

### 2.1 `pypost/core/worker.py`

#### Change: replace `_is_stopped` with `_stop_event`

```
BEFORE                          AFTER
------                          -----
import (no threading)           import threading

__init__:                       __init__:
  self._is_stopped = False        self._stop_event = threading.Event()

stop():                         stop():
  self._is_stopped = True          self._stop_event.set()

run():                          run():
  self._is_stopped = False         # no reset here — event was cleared in __init__
  ...                              ...
  def check_stop():                def check_stop():
      return self._is_stopped          return self._stop_event.is_set()
```

**Invariant enforced by this design:**
- `_stop_event` is cleared exactly once: in `__init__`.
- `_stop_event` is set by `stop()` only.
- `run()` never touches `_stop_event` directly; it reads it only through the `check_stop` closure.
- Satisfies REQ-1.1 through REQ-1.5 and AC-1 through AC-3.

#### No other changes to `worker.py`

Signals, constructor signature, `run()` logic, and error handling are untouched (REQ-4.1, REQ-4.2, REQ-4.3, AC-8).

---

### 2.2 `pypost/ui/presenters/tabs_presenter.py`

Only `_handle_send_request` changes. All other methods are untouched.

#### New send-request flow

```
_handle_send_request(request_data):

  1. Find sender_tab (unchanged).

  2. Guard — stale reference cleanup (NEW):
     if sender_tab.worker is not None and not sender_tab.worker.isRunning():
         # Worker finished but _reset_tab_ui_state has not been called yet.
         # Clean up the stale reference so we can create a fresh worker.
         sender_tab.worker = None

  3. Guard — active worker (unchanged behaviour, now also covers RC-4):
     if sender_tab.worker is not None and sender_tab.worker.isRunning():
         # Cancel path — stop the running worker, update button, return.
         ...
         return

  4. Log + metrics (unchanged).

  5. Update UI to "Stop" state (unchanged — happens BEFORE worker.start()).

  6. Resolve collection_name (unchanged).

  7. Construct RequestWorker (unchanged).

  8. Connect all signals (unchanged).

  9. Assign worker reference BEFORE starting (CHANGED ORDER):
     sender_tab.worker = worker   ← moved up from after start()

  10. Start the worker:
      worker.start()              ← moved down from before assignment
```

**Why this ordering matters for RC-3 and RC-4:**

Step 9 sets `sender_tab.worker` before the thread begins execution. If a second send event fires between steps 9 and 10 (the thread has not yet started, so `isRunning()` is `False`), the stale-reference cleanup in step 2 runs, nulls the reference, and a new worker is created. This is safe because the previous worker has not yet called `start()`, so starting it again would be undefined — but in practice, since the presenter now owns the new worker reference before calling `start()`, the old worker object becomes unreferenced and Qt's `deleteLater` connections clean it up.

However, in the normal operating window the event loop is single-threaded, so two send events cannot be processed simultaneously. The ordering fix primarily closes RC-3.

**Why the stale-reference cleanup (step 2) is needed for RC-3:**

Without it, a worker that has finished (IsRunning() → False) but whose `_reset_tab_ui_state` callback has not yet been dispatched through the Qt event loop would leave `sender_tab.worker` pointing to a dead thread. The guard in step 3 would not fire (isRunning() is False), and a second worker would be created.

**AC-5 compliance:**

`send_btn.setText("Stop")` is already called before `worker.start()` in the existing code (line 333). This satisfies AC-5 ("disabled or set to Cancel state before worker.start()"). No additional button state change is required.

---

### 2.3 New test file: `tests/test_worker_race.py`

Three new test cases are required (REQ-5.2a, REQ-5.2b, REQ-5.2c):

#### REQ-5.2a — `stop()` before `run()` cancels the request

```python
def test_stop_before_run_check_stop_is_true():
    worker = _make_worker()
    worker.stop()                    # called before run()
    with patch.object(worker.service, "execute", return_value=_ok_result()) as mock_exec:
        worker.run()
    # The check_stop callable passed to execute must return True immediately.
    call_kwargs = mock_exec.call_args.kwargs
    assert call_kwargs["stop_flag"]() is True
```

**Implementation note:** `check_stop` is a closure capturing `self._stop_event`. After `stop()` sets the event, `_stop_event.is_set()` returns `True`. Since `run()` no longer clears the event, `check_stop()` returns `True` on the first poll inside `execute`.

#### REQ-5.2b — `stop()` call is never overwritten by concurrent `run()`

```python
def test_stop_flag_not_overwritten_after_stop():
    worker = _make_worker()
    worker.stop()
    # Simulate run() executing — it must not clear the stop event
    captured_check_stop = None
    def capture_stop_flag(**kwargs):
        nonlocal captured_check_stop
        captured_check_stop = kwargs["stop_flag"]
        return _ok_result()
    with patch.object(worker.service, "execute", side_effect=capture_stop_flag):
        worker.run()
    assert captured_check_stop() is True
```

#### REQ-5.2c — Second send while worker running does not create a second worker (presenter level)

```python
def test_second_send_while_running_does_not_create_second_worker():
    p = _make_presenter()
    p.add_new_tab(request_data)
    tab = p.widget.widget(0)

    fake_worker = MagicMock()
    fake_worker.isRunning.return_value = True
    tab.worker = fake_worker

    # Fire a second send event while worker appears running
    with patch("pypost.ui.presenters.tabs_presenter.RequestWorker") as MockWorker:
        p._handle_send_request(request_data)
        MockWorker.assert_not_called()   # no new worker must be created
```

---

## 3. Files Changed

| File | Change type | Scope |
|---|---|---|
| `pypost/core/worker.py` | Modify | `__init__`, `stop()`, `run()` — 4 lines changed |
| `pypost/ui/presenters/tabs_presenter.py` | Modify | `_handle_send_request` — stale cleanup + assignment order |
| `tests/test_worker_race.py` | Create | 3 new test cases for REQ-5.2a/b/c |

---

## 4. Constraints Verified

| Constraint | Satisfied by |
|---|---|
| REQ-4.4: No changes to `RequestService`, `HTTPClient`, models | Only `worker.py` and `tabs_presenter.py` modified |
| REQ-5.1: Existing tests unchanged | `test_worker.py` calls `worker.run()` directly; `run()` still works — `_stop_event` starts cleared |
| AC-3: No lock, busy-wait, or sleep | Only `threading.Event` used |
| AC-6: All existing tests pass | `_is_stopped` attribute removed; existing tests do not access it directly |

**Note on existing tests:** `test_worker.py` patches `worker.service.execute` and calls `worker.run()` directly. None of the three existing tests access `_is_stopped`. The refactoring to `_stop_event` is transparent to them. Verified by inspection.

---

## 5. Sequence Diagram — Happy Path After Fix

```
Main Thread                     Worker Thread
-----------                     -------------
RequestWorker.__init__()
  _stop_event = Event()  (cleared)

[optional] stop()
  _stop_event.set()

sender_tab.worker = worker    ← assigned before start
worker.start()
                                run() called by Qt
                                  check_stop = lambda: _stop_event.is_set()
                                  service.execute(..., stop_flag=check_stop)
                                  → check_stop() returns True  (if stop was called)
                                  finished/error signal emitted

_on_request_finished / _on_request_error
  _reset_tab_ui_state(tab)
    sender_tab.worker = None
    send_btn re-enabled
```
