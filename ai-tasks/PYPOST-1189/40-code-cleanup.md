# Code Cleanup: PYPOST-1189

## Static Analysis & Quality Gate

- `make lint`: Passed with zero warnings/errors.
- Target test suite `tests/test_tabs_presenter.py`: Passed cleanly.

## Changes Made

- Added `test_close_saved_websocket_tab_with_edited_url_does_not_prompt`: verified that collection-backed WebSocket tabs with modified URLs close without triggering `prompt_unsaved_draft_tab_close`.
- Added `test_is_websocket_draft_dirty_editor_snapshots`: locked dirty detection across URL, params, headers, subprotocols, MCP expose checkbox, and MCP description.
- Added `test_save_tabs_state_mixed_saved_and_draft_websocket_tabs`: locked mixed state persistence in `TabsPresenter`.

## Unused Code / Refactoring

- No production code modified; tests confirm existing implementation contracts.
