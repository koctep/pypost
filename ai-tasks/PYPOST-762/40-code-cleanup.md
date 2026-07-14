# PYPOST-762: Code Cleanup

## Scope

Single focused change set; no unrelated refactors.

## Checks

- Line length within 100 characters.
- New keyword-only `defer_initial_load` follows `RequestManager` convention.
- Thread locks separated: `_lock` for entries, `_load_state_lock` for load lifecycle.
- `HistoryPanel` unchanged — refresh contract preserved; empty-first paint is acceptable.

## Files reviewed

| File | Notes |
| --- | --- |
| `pypost/core/history_manager.py` | Load/save lock separation; no duplicate helpers |
| `pypost/ui/main_window.py` | `QTimer.singleShot` marshals refresh to UI thread |
| `tests/test_history_manager.py` | Module-level `pytestmark` timeout retained |
