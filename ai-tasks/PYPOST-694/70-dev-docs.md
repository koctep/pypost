# PYPOST-694: Developer Documentation

## Summary

Documented `HistoryManager` in the composition-root table and MainWindow injectable
dependencies in `doc/dev/testability.md`. Updated `doc/dev/architecture.md` to note
`HistoryManager` is wired from `main.py` (PYPOST-694).

## Files Updated

| File | Change |
| --- | --- |
| `doc/dev/testability.md` | Added `HistoryManager` row; MainWindow `history_manager` param |
| `doc/dev/architecture.md` | Removed `HistoryManager` from MainWindow-constructed list |

## Production wiring

```python
history_manager = HistoryManager()
window = MainWindow(..., history_manager=history_manager)
```

Tests should inject `MagicMock(spec=HistoryManager)` or a temp-path `HistoryManager` rather
than patching the class at `main_window`.
