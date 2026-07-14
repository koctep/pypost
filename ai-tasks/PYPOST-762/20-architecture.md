# PYPOST-762: Architecture — Deferred HistoryManager startup load

## Design

Mirror `RequestManager(defer_initial_load=True)`:

| Component | Change |
| --- | --- |
| `HistoryManager` | `defer_initial_load` skips `_load()` in `__init__`; `load_async()` reads in daemon thread |
| `main.py` | `HistoryManager(defer_initial_load=True)` at composition root |
| `MainWindow` | `wire_presenter_signals` dispatches async load; `QTimer.singleShot` → `HistoryPanel.refresh` |

## Data flow

```text
main.py
  HistoryManager(defer_initial_load=True)   # empty memory
  MainWindow(..., history_manager=...)
    HistoryPanel.refresh()                  # empty list at first paint
    load_async(on_complete → refresh)     # daemon thread reads history.json
         │
         ▼
    HistoryPanel.refresh()                  # populated list on UI thread
```

## Mutations during async load

`append`, `delete_entry`, and `clear` call `_ensure_loaded()` which joins the in-flight load
thread before mutating, preventing lost or overwritten entries.

`get_entries()` returns the current in-memory snapshot without forcing load (empty until async
completes).

## Affected files

| File | Change |
| --- | --- |
| `pypost/core/history_manager.py` | `defer_initial_load`, `load_async`, `_ensure_loaded` |
| `pypost/main.py` | Deferred construction |
| `pypost/ui/main_window_signals.py` | Startup dispatch + UI-thread refresh |
| `tests/test_history_manager.py` | Deferred load tests |
| `doc/dev/performance_audit.md` | Thread model table update |
