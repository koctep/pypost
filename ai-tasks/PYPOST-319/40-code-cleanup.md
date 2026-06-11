# PYPOST-319: Code Cleanup Report

## Summary

Added incremental save-as tree updates by extracting shared item builders from `refresh_tree`.
No new linter issues; line length within 100 characters.

## Files Changed

| File | Change |
|------|--------|
| `pypost/ui/presenters/collections_presenter.py` | Item builders, `add_saved_request_to_tree` |
| `pypost/ui/presenters/tabs_presenter.py` | `request_save_as_completed` signal |
| `pypost/ui/main_window.py` | Save-as wiring |
| `tests/test_collections_presenter.py` | Three incremental insert tests |
| `tests/test_tabs_presenter.py` | Save-as signal routing test |

## Cleanup Actions Performed

- Deduplicated collection/request item construction between refresh and incremental paths.
- Updated `request_saved` comment to reflect refresh (not reload).
- No unused imports; no dead code introduced.

## Validation Results

- [x] All targeted tests passed
- [x] Syntax valid
- [x] Line length ≤ 100 characters

## Notes

`refresh_tree()` remains the path for regular save and explicit full rebuilds.
