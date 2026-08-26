# Roadmap: PYPOST-1160

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1160/10-requirements.md`
  - Implementation language recorded: Python
  - Scope: Collections sidebar context menu parity for WebSocket profiles
    (**New tab**, **Rename**, **Delete**); open-tab lifecycle when a profile
    is deleted
  - Depends on WS-TM-2
    ([PYPOST-1158](https://pypost.atlassian.net/browse/PYPOST-1158)) — blank
    WebSocket draft tab shipped
  - ACs: right-click opens **New tab**, **Export Collection…**, **Rename**,
    **Delete** on WebSocket rows; **New tab** always adds an isolated tab
    copy with its own live session; **Rename** persists and updates open tab
    titles; **Delete** confirms, removes the profile, and closes or prompts
    on bound tabs (warn when unsaved edits or active connection); deleting a
    collection affects contained WebSocket profiles and their open tabs;
    left-click focus/dedup unchanged; WebSocket rename/delete and
    collections-context **New tab** telemetry parity with HTTP
  - Awaiting user review before STEP 1 gate (`[x]`)
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1160/20-architecture.md`
  - HTTP reference: `CollectionTreeActions` menu pipeline; gap is
    `_resolve_item_target` ignores `WebSocketConnection`
  - Plan: isolated WS tab API (`open_websocket_isolated_tab` +
    `copy_websocket_for_isolated_tab`); websocket rename/delete/close signals;
    `WebSocketRegistry` in dispatch context; delete prompt for unsaved/active
    sessions; `protocol=websocket` on collections-context new-tab metric
  - Step 3 red tests: 9 proposed cases in architecture doc (menu parity,
    isolated insert, rename labels, delete prompt, collection cascade)
  - Awaiting user review before STEP 2 gate (`[x]`)
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_collection_tree_actions.py::TestCollectionTreeActionsWebSocket::test_websocket_menu_offers_new_tab_export_rename_delete`
  - [x] `tests/test_collection_tree_actions.py::TestCollectionTreeActionsWebSocket::test_websocket_new_tab_emits_isolated_open_with_protocol_metric`
  - [x] `tests/test_collection_tree_actions.py::TestCollectionTreeActionsWebSocket::test_delete_websocket_emits_websockets_deleted`
  - [x] `tests/test_collection_tree_actions.py::TestCollectionTreeActionsWebSocket::test_delete_collection_emits_all_websocket_ids`
  - [x] `tests/test_tabs_presenter.py::TestTabsPresenterWebSocketCollections::test_open_websocket_isolated_tab_always_inserts_second_tab`
  - [x] `tests/test_tabs_presenter.py::TestTabsPresenterWebSocketCollections::test_open_websocket_isolated_tabs_have_independent_presenters`
  - [x] `tests/test_tabs_presenter.py::TestTabsPresenterWebSocketCollections::test_rename_websocket_tabs_updates_labels`
  - [x] `tests/test_tabs_presenter.py::TestTabsPresenterWebSocketCollections::test_close_tabs_for_websocket_ids_silent_when_clean_idle`
  - [x] `tests/test_tabs_presenter.py::TestTabsPresenterWebSocketCollections::test_close_tabs_for_websocket_ids_prompts_when_connected`
- [x] **STEP 4: Development**
  - [x] `_resolve_item_target` recognizes `WebSocketConnection`; menu New tab / rename label sync / `_affected_websocket_ids`
  - [x] `copy_websocket_for_isolated_tab`, snapshot/equality helpers in `websocket_persisted_fields.py`
  - [x] `open_websocket_isolated_tab`, `rename_websocket_tabs`, `close_tabs_for_websocket_ids` in `TabsPresenter`; WS rename/close logic extracted to `tabs_presenter_ws_close.py`; request bulk-close to `tabs_presenter_request_close.py`
  - [x] `is_websocket_saved_tab_dirty`, `prompt_deleted_websocket_profile_tab_close`, `persisted_baseline` on `WebSocketTab`
  - [x] Collections signals (`open_websocket_in_isolated_tab`, `websocket_renamed`, `websockets_deleted`) and `main_window_signals` wiring
  - [x] `RequestManager._item_dispatch_context` supplies `WebSocketRegistry` for websocket rename/delete dispatch
  - [x] All 9 Step 3 reds green (`make test` with WebSocket collections `-k` filter)
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1160/40-code-cleanup.md`
  - `make lint` clean; no code changes required
  - WS collections tests green (`TestCollectionTreeActionsWebSocket`,
    `TestTabsPresenterWebSocketCollections`)
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1160/50-observability.md`
  - `collection_websocket_open_new_tab` INFO; `close_tabs_for_deleted_websockets`
  - `gui_new_tab_actions_total` with `protocol=websocket` on collections New tab
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1160/60-tech-debt.md`
  - [PYPOST-1184](https://pypost.atlassian.net/browse/PYPOST-1184) still open (To Do)
  - No AC-breaking debt; PYPOST-1161 / PYPOST-1163 remain epic deferrals
- [x] **STEP 8: Dev Docs**
  - `doc/dev/websocket_collections_menu.md`
  - `doc/dev/collection_tree_actions.md` — WebSocket row parity
  - `doc/dev/README.md` TOC entry
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1160/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1160/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1160/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1160/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1160/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
