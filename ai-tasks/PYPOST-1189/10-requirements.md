# Requirements: PYPOST-1189

## Task Metadata

- **Issue**: PYPOST-1189
- **Title**: [PYPOST-1158] Lock saved WebSocket skip-prompt and non-URL draft dirty tests
- **Language**: Python
- **Type**: Debt / Test Coverage
- **Source**: `ai-tasks/PYPOST-1158/60-tech-debt.md` (item 5)

## Problem Statement

After PYPOST-1158, dirty-close tests only cover unsaved drafts with URL edits. The following coverage gaps remain:
1. Collection-backed (saved) WebSocket tabs with modified editor URL must NOT call `prompt_unsaved_draft_tab_close` upon tab close.
2. `is_websocket_draft_dirty` must detect editor modifications across params, headers, subprotocols, and MCP expose checkbox / description in addition to URL.
3. Presenter `save_tabs_state` must correctly handle mixed open tabs: persisting saved WebSocket tab IDs while omitting unsaved draft WebSocket tab IDs.

## Functional Requirements

- **FR-1**: Saved WebSocket Tab Close Non-Prompting
  - When closing a collection-backed WebSocket tab whose editor URL has been changed, `prompt_unsaved_draft_tab_close` must NOT be invoked and the tab must close directly.
- **FR-2**: Unsaved Draft Dirty Detection for Non-URL Fields
  - `is_websocket_draft_dirty` must return `True` if any of params, headers, subprotocols, `expose_as_mcp`, or `mcp_description` differ from default empty/factory state.
  - `is_websocket_draft_dirty` must return `False` when all editor fields remain at default empty/factory state.
- **FR-3**: Mixed Tabs Persistence Gate
  - When saving tabs state with both a collection-backed WebSocket tab and a blank unsaved WebSocket draft tab open, the saved WebSocket tab ID must be persisted into `open_tabs` and the draft ID must be omitted.

## Acceptance Criteria

1. Test locks that closing a saved WebSocket tab with edited URL does not prompt.
2. Test locks that `is_websocket_draft_dirty` detects dirty params, headers, subprotocols, and MCP checkbox.
3. Test locks mixed draft + saved `save_tabs_state`.
4. All existing and new tests pass cleanly with 100% compliance.
