# PYPOST-47: Code Cleanup Report

## Summary

Refactored collection loading to separate RequestManager reads from tree UI rebuild. No linter
issues introduced; line length within 100 characters.

## Files Changed

| File | Change |
|------|--------|
| `pypost/ui/presenters/collections_presenter.py` | Added `refresh_tree()`; post-CRUD uses refresh |
| `pypost/ui/main_window.py` | Startup and `request_saved` use `refresh_tree` |
| `tests/test_collections_presenter.py` | Two new tests for refresh/reload split |
| `tests/test_main_window.py` | Startup wiring test |

## Cleanup Actions Performed

- Removed redundant disk reload on post-save and post-CRUD tree updates.
- Renamed log event from `load_collections_completed` to `refresh_tree_completed` for UI-only path.
- No unused imports added; no dead code introduced.

## Validation Results

- [x] All tests passed
- [x] No merge conflicts
- [x] Syntax valid
- [x] Line length ≤ 100 characters

## Notes

`load_collections()` retained as public API for explicit disk resync; callers that need fresh
disk state should use it; hot paths should prefer `refresh_tree()`.
