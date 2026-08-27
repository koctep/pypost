# Architecture: PYPOST-1191

## Overview

PYPOST-1191 optimizes `WebSocketRegistry` and `McpClientRegistry` construction during `save_tabs_state` and `close_tab` operations by binding a single registry instance to the predicate closure passed to `collect_persistable_open_tab_ids` and `close_workspace_tab`.

## Implementation Details

1. **`pypost/ui/presenters/tabs_presenter_draft.py`**:
   - Add `make_websocket_saved_predicate(request_manager: RequestManager) -> Callable[[str], bool]`.
   - Add `make_mcp_client_saved_predicate(request_manager: RequestManager) -> Callable[[str], bool]`.
   - Update `websocket_id_is_saved` and `mcp_client_id_is_saved` to support optional `registry` keyword argument.

2. **`pypost/ui/presenters/tabs_presenter.py`**:
   - In `save_tabs_state`, use `make_websocket_saved_predicate` and `make_mcp_client_saved_predicate`.

3. **`pypost/ui/presenters/tabs_presenter_close.py`**:
   - In `close_workspace_tab`, use `make_websocket_saved_predicate`.

4. **`tests/test_tabs_presenter.py`**:
   - Add a test verifying single `WebSocketRegistry` instantiation during `save_tabs_state` with multiple open WebSocket tabs.
