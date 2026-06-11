# PYPOST-417 — Architecture

## Current lifecycle

```
TabsPresenter._handle_send_request
  → new RequestWorker(...)
  → tab.worker = worker
  → worker.start()
  → [optional] worker.stop()  → _stop_event.set()  (permanent)
  → finished/error → _clear_tab_worker()
```

`TabsPresenter` never calls `start()` twice on the same instance. Each tab send allocates a new
`RequestWorker`.

## Change plan

| Layer | Change |
|-------|--------|
| `pypost/core/worker.py` | Class docstring + expanded `stop()` docstring |
| `tests/test_worker_race.py` | `test_worker_not_reusable_after_stop` |
| `doc/dev/request_execution.md` | Subsection under tab worker lifecycle |

No presenter or signal changes.

## Test design

1. Create worker, call `stop()`.
2. Call `run()` once — assert `stop_flag()` is True (existing behaviour).
3. Call `run()` again on the **same** instance — assert `stop_flag()` still True.

This documents that `_stop_event` is never cleared without requiring Qt thread integration.
