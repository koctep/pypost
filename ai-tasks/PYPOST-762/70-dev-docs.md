# PYPOST-762: Dev Docs

## Updated documentation

- `doc/dev/performance_audit.md` — Collection and History I/O table and thread model list
  now reflect deferred `HistoryManager` startup load (PYPOST-762).

## Key behavior (for developers)

```python
# Composition root (main.py)
history_manager = HistoryManager(defer_initial_load=True)

# MainWindow startup (via wire_presenter_signals)
history_manager.load_async(on_complete=lambda: QTimer.singleShot(0, history_panel.refresh))
```

Tests continue to use synchronous load via `_manager_at()` helper (default `defer_initial_load=False`).
