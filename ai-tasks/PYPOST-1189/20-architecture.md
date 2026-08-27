# Architecture: PYPOST-1189

## Overview

PYPOST-1189 adds test locks for saved WebSocket tab close behavior, editor-snapshot field dirty detection (`is_websocket_draft_dirty`), and mixed saved/draft persistence in `TabsPresenter`.

## Design & Test Strategy

1. **Saved Tab Prompt Skip**:
   - In `tests/test_tabs_presenter.py`, open a collection-backed `WebSocketTab` via `p.open_websocket_tab(conn)`.
   - Modify the tab's `connection_editor.url_input.setText("wss://modified.example.com")`.
   - Call `p.close_tab(idx)` within a patched `prompt_unsaved_draft_tab_close` context.
   - Assert `prompt_unsaved_draft_tab_close` is NOT called, and tab is closed.

2. **Editor-Snapshot Dirty Detection**:
   - In `tests/test_tabs_presenter.py`, create a blank WebSocket draft tab via `p.add_blank_websocket_tab()`.
   - Verify `is_websocket_draft_dirty(tab)` is initially `False`.
   - Mutate each editor field sequentially (params table, headers table, subprotocols input, MCP expose checkbox, MCP description input) and assert `is_websocket_draft_dirty(tab)` becomes `True`.

3. **Mixed Tab State Persistence**:
   - In `tests/test_tabs_presenter.py`, create a presenter with both a saved collection-backed WebSocket tab (`open_websocket_tab`) and an unsaved blank WebSocket tab (`add_blank_websocket_tab`).
   - Call `p.save_tabs_state()`.
   - Assert that the saved ID is present in `_state_manager.get_open_tabs()` and the draft ID is absent.

## Impact Analysis

- Changes are test-only in `tests/test_tabs_presenter.py`.
- No modifications needed to production code if tests confirm existing contracts.
