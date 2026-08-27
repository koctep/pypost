# Code Cleanup: PYPOST-1190

## Static Analysis & Quality Gate

- `make lint`: Passed with zero warnings/errors.
- Target test suite `tests/test_tabs_presenter.py`: All 118 tests passed.

## Changes Made

- `pypost/core/request_persisted_fields.py`: Added `factory_request_draft()` and `request_draft_fields_equal()`.
- `pypost/ui/presenters/tab_dirty.py`: Added `is_request_draft_dirty()` and updated `is_tab_dirty()` to evaluate draft dirty status for unsaved request tabs.
- `pypost/ui/presenters/tabs_presenter_draft.py`: Added `confirm_close_request_draft()` with Discard / Keep dialog and structured logging.
- `pypost/ui/presenters/tabs_presenter_close.py`: Integrated `confirm_close_request_draft()` into `close_workspace_tab()`.
- `tests/test_tabs_presenter.py`: Added unit and observability tests covering HTTP draft close prompt behavior, clean close, and dirty field snapshot detection.

## Unused Code / Refactoring

- Kept presenter line count within audit caps by placing close logic in existing helper modules.
