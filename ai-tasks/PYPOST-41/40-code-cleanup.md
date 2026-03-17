# PYPOST-41 Code Cleanup

## Summary

Implementation of PYPOST-41 (Request Logging for History Viewing) is complete.
All files comply with project standards (UTF-8, LF, ≤100-char lines, no trailing whitespace).

## Files Changed / Created

| File | Type | Notes |
|------|------|-------|
| `pypost/models/models.py` | Modified | Added `HistoryEntry` Pydantic model |
| `pypost/core/history_manager.py` | New | `HistoryManager` with thread-safe load/save/append/delete/clear |
| `pypost/core/request_service.py` | Modified | Injected `HistoryManager`; extended `execute()` with history recording |
| `pypost/core/worker.py` | Modified | Added `history_manager` + `collection_name` constructor params |
| `pypost/ui/presenters/tabs_presenter.py` | Modified | Added `history_manager` param, `request_executed` signal, `load_request_from_history()` |
| `pypost/ui/widgets/history_panel.py` | New | Qt sidebar widget with list, filter, detail pane and context menu |
| `pypost/ui/main_window.py` | Modified | Instantiates `HistoryManager`, wires `HistoryPanel` into sidebar `QTabWidget` |
| `tests/test_history_manager.py` | New | 9 unit tests covering load, append, cap, delete, clear, persistence, concurrency |
| `tests/test_request_service.py` | Modified | 5 new tests for history recording logic |

## Cleanup Actions Performed

### Deprecation fix
- Replaced `datetime.utcnow()` (deprecated in Python 3.12) with
  `datetime.now(timezone.utc)` in `request_service.py`.

### Import organisation
- All new imports follow the existing convention: stdlib → third-party → local, separated by a
  blank line where the original file already used that style.

### No leftover debug code
- No `print()` statements introduced; all diagnostic output uses `logger`.

### Line-length compliance
- All lines verified ≤ 100 characters.

### Unused imports
- None introduced.

## Test Results

```
61 passed in 3.50s  (non-Qt subset)
24 passed in 4.11s  (history + request_service tests only)
```

No failures, no warnings after the `datetime.utcnow()` fix.
