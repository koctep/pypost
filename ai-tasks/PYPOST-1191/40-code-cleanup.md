# Code Cleanup: PYPOST-1191

## Static Analysis & Quality Gate

- `make lint`: Passed cleanly with zero warnings/errors.
- Target test suite `tests/test_tabs_presenter.py`: All 120 tests passed.

## Changes Made

- `pypost/ui/presenters/tabs_presenter_draft.py`: Added `make_websocket_saved_predicate` and `make_mcp_client_saved_predicate` to bind a single registry instance per batch operation.
- `pypost/ui/presenters/tabs_presenter.py`: Updated `save_tabs_state` to reuse bound predicate closures.
- `pypost/ui/presenters/tabs_presenter_close.py`: Updated `close_workspace_tab` to use `make_websocket_saved_predicate`.
- `tests/test_tabs_presenter.py`: Added regression test asserting single registry instantiation per `save_tabs_state` iteration.

## Unused Code / Refactoring

- Kept `websocket_id_is_saved` and `mcp_client_id_is_saved` signatures backwards compatible by adding optional `registry` parameters.
