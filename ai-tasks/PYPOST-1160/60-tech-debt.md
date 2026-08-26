# PYPOST-1160: Technical Debt Analysis

PYPOST-1160 (WS-TM-4) shipped Collections WebSocket context-menu parity:
**New tab**, **Rename**, **Delete**, collection-delete tab lifecycle, and
`protocol=websocket` on collections-context new-tab metrics. There is **no
AC-breaking debt** in this story's change. Remaining items are intentional epic
deferrals, presenter LOC headroom consumed by prior stories, and follow-ups
already ticketed elsewhere.

Phase D of the orchestrator creates Jira issues. This step does not.
New follow-ups omit browse links unless a key already exists for context.

## Shortcuts Taken

1. **Parallel HTTP vs WebSocket signals instead of overloaded `requests_deleted`.**
   `websockets_deleted` / `websocket_renamed` mirror the HTTP pair to avoid
   regressing HTTP tab wiring. Slightly more signal surface in
   `CollectionsPresenter` and `main_window_signals.py`.

2. **Isolated copy preserves profile id (not a new collection row).**
   `copy_websocket_for_isolated_tab` deep-copies fields but keeps the saved
   `id` so tab binding and open-tabs persistence stay consistent with HTTP
   isolated tabs. Multiple tabs can share one profile id with independent
   sessions — by design (FR-2.2, FR-2.3).

3. **HTTP delete tab close stays silent; WebSocket delete prompts only.**
   `close_tabs_for_request_ids` unchanged. WebSocket delete uses
   `prompt_deleted_websocket_profile_tab_close` when unsaved edits or an active
   session are detected. HTTP session-aware delete prompts remain out of scope.

4. **User-facing docs deferred to PYPOST-1163.**
   `doc/user/collections.md` claims are now true in code; full user doc pass
   is not this story. Developer docs land in Step 8.

5. **`RequestManager._item_dispatch_context` lazy-imports `WebSocketRegistry`.**
   Fixes websocket rename/delete dispatch without changing strategy modules.
   Each dispatch constructs a registry and rebuilds the index — correct and
   cheap for GUI collections; wasteful if called in a tight loop (not today).

## Code Quality Issues

- **`tabs_presenter.py` is 779 / 785 LOC** after Step 4 extracts
  (`tabs_presenter_ws_close.py`, `tabs_presenter_request_close.py`). Headroom
  exists for small edits, but the shared insert-before-plus helper is **not**
  extracted here. [PYPOST-1184](https://pypost.atlassian.net/browse/PYPOST-1184)
  remains **To Do** — do not close that ticket in this story.

- **`_connection_from_websocket_tab` split snapshot** (editor vs model fields)
  is shared between draft-dirty and saved-profile-dirty paths. PYPOST-1161
  save should consolidate into one persisted snapshot reader rather than
  adding a third comparison path.

- **`websocket_id_is_saved` rebuilds registry per lookup** in
  `save_tabs_state` / `_insert_websocket_tab` — inherited from PYPOST-1158;
  bind one registry per presenter operation when someone next touches draft
  persist helpers.

- **`collection_tree_actions.py` grew to 434 LOC** with websocket branches.
  Still under project module norms; no extract required unless MCP Client menu
  parity (PYPOST-1164) adds more branches — consider a small dispatch table
  then.

Hardcoded dialog copy (**Close tab**, **Keep the tab**, **WebSocket profile
deleted**) matches FR-5.3 wording in requirements.

## Missing Tests

Covered by Step 3 / Step 4 (9 automated cases):

- Menu parity, isolated open + metric, rename tab labels, delete emit ids,
  collection cascade, silent close vs connected prompt.

**Not covered (acceptable deferrals):**

- End-to-end presenter integration: full `CollectionsPresenter` right-click
  on a live tree with real `RequestManager` + disk persistence (isolated harness
  covers menu dispatch).
- Rename inline delegate E2E for websocket rows (HTTP/collection E2E exists;
  websocket rename reuses the same delegate path).
- `test_delete_open_tabs_integration.py` collection-delete closes WS tabs —
  listed in architecture as optional; close logic tested in
  `TestTabsPresenterWebSocketCollections`.

All PYPOST-1160 tests use explicit timeout markers via the shared presenter
harness.

## Performance Concerns

None for typical collections sizes. `close_tabs_for_websocket_ids` scans all
open tabs once per delete event — same pattern as HTTP
`close_tabs_for_request_ids`. `persisted_websocket_fields_equal` compares full
persisted field sets including presets/sequences; acceptable for GUI delete
prompts.

## Follow-up Tasks

Pre-existing / epic deferrals (not blocking Step 8):

1. **Extract shared insert-before-plus helper** — shrink
   `add_new_tab`, `_insert_websocket_tab`, and `add_blank_mcp_client_tab`
   factories before the cap blocks future tab types.
   - Jira: [PYPOST-1184](https://pypost.atlassian.net/browse/PYPOST-1184) — **still open (To Do)**

2. **WebSocket save / Save As to collection** — `persisted_baseline` adoption
   on first save, factory-compare retirement for saved profiles.
   - Jira: [PYPOST-1161](https://pypost.atlassian.net/browse/PYPOST-1161)

3. **User documentation pass** — `doc/user/collections.md` WebSocket menu
   examples and delete-safety copy.
   - Jira: [PYPOST-1163](https://pypost.atlassian.net/browse/PYPOST-1163)

4. **HTTP collections New tab `protocol=http` metric** — HTTP menu still records
   `protocol=unknown` on `track_gui_new_tab_action("collections_context")`;
   align when touching HTTP collections telemetry.

5. **MCP Client collections menu parity** — `_resolve_item_target` pattern debt
   for non-request items (see PYPOST-1164 audit).

**NON-BLOCKER — pre-existing** (not caused by PYPOST-1160):

- `tests/test_solid_audit_baseline.py` — baseline metric drift unrelated to WS
  collections menu (full `make test` may fail this file; filtered WS suites pass).
