# Requirements: PYPOST-1191

## Task Metadata

- **Issue**: PYPOST-1191
- **Title**: [PYPOST-1158] Reuse one WebSocketRegistry per save_tabs_state/close_tab
- **Language**: Python
- **Type**: Debt / Performance Optimization
- **Source**: `ai-tasks/PYPOST-1158/60-tech-debt.md` (item 7)

## Problem Statement

In `TabsPresenter.save_tabs_state()` and `close_tab()`, checking whether a WebSocket tab is collection-backed previously called `websocket_id_is_saved`, which instantiated a new `WebSocketRegistry` on every invocation. Because `WebSocketRegistry.__init__` calls `rebuild_index()`, iterating over multiple open WebSocket tabs rebuilt the collection index once per tab.

## Functional Requirements

- **FR-1**: Single Registry Binding per Bulk Operation
  - Provide `make_websocket_saved_predicate(request_manager)` (and `make_mcp_client_saved_predicate(request_manager)`) in `pypost.ui.presenters.tabs_presenter_draft`.
  - The returned callable must reuse a single `WebSocketRegistry` / `McpClientRegistry` instance across multiple lookup calls.
- **FR-2**: Integration into Presenter Workflows
  - `TabsPresenter.save_tabs_state()` must bind one predicate via `make_websocket_saved_predicate` and `make_mcp_client_saved_predicate`.
  - `close_workspace_tab()` must bind one predicate via `make_websocket_saved_predicate`.
- **FR-3**: Backwards Compatibility
  - `websocket_id_is_saved(request_manager, ws_id)` and `mcp_client_id_is_saved(request_manager, profile_id)` must remain available and accept an optional `registry` argument.

## Acceptance Criteria

1. `save_tabs_state()` constructs `WebSocketRegistry` and `McpClientRegistry` at most once per execution, regardless of how many tabs are open.
2. `close_workspace_tab()` constructs `WebSocketRegistry` at most once per execution.
3. Unit tests verify that multiple tab iterations instantiate `WebSocketRegistry` exactly once.
4. All existing tab persistence and closing tests pass.
