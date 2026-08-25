# PYPOST-1157: Technical Debt Analysis

PYPOST-1157 (WS-TM-1) shipped the blank-tab protocol picker and routing API
described in `20-architecture.md`. There is **no AC-breaking debt** in this
story's own change. Remaining items are intentional epic deferrals, documented
testability shortcuts, a module-size capacity risk, and pre-existing suite
instability found during the run. None of those items block Step 8.

## Shortcuts Taken

1. **Injectable picker instead of live `QMenu.exec()` in tests.** Architecture
   (R-2 / Testability) requires this: real `exec()` blocks the Qt event loop.
   `TabsPresenter` takes `protocol_picker`; production default is
   `NewTabProtocolPicker().prompt`. Presenter tests, plus-click tests, and
   `tests/test_agent_golden_e2e.py` inject HTTP (or cancel / WebSocket).
   `tests/test_new_tab_protocol_picker.py` is construction-only (`build_menu`,
   no `exec()`). CI therefore never exercises the live popup, Enter-to-confirm,
   Esc/click-away, or `prompt()` action-data mapping. Keyboard default is
   still asserted via `setActiveAction` on the built menu.
2. **WebSocket confirm is a placeholder `WebSocketTab`.** Confirming WebSocket
   calls `add_blank_websocket_tab()` → `WebSocketConnection()` (name
   `"New WebSocket"`, empty URL, unique UUID) + existing `WebSocketTab`. Full
   draft-editor semantics, MCP preview on draft, and session-restore exclusion
   are [PYPOST-1158](https://pypost.atlassian.net/browse/PYPOST-1158). Blank
   WS tabs with a default id **are** written by `save_tabs_state()` today.
   This is in-scope for WS-TM-1 (FR-4.3). Do not treat it as incomplete 1157
   work.
3. **MCP Client is not a picker item.** Menu is **HTTP Request** then
   **WebSocket** only. [PYPOST-1165](https://pypost.atlassian.net/browse/PYPOST-1165)
   adds the third item. Do not treat it as incomplete 1157 work.
4. **Close-last-tab / empty-workspace fallback stays HTTP-only.** `close_tab`
   and `close_tabs_for_request_ids` still call `add_new_tab(save_state=False)`
   when `_request_tab_count() == 0`. FR-5.2 / architecture out-of-scope;
   [PYPOST-1159](https://pypost.atlassian.net/browse/PYPOST-1159) owns picker
   reuse on that path.
5. **Collections **New tab** still emits `protocol=unknown`.**
   `collection_tree_actions` calls `track_gui_new_tab_action("collections_context")`
   with the default protocol. Architecture R-3 / R-4 allowed this so
   non-picker callers keep compiling. FR-6 applies to completed picker
   choices (`http` / `websocket`), not this path.
6. **User-facing docs not rewritten here.** `doc/user/websocket.md` step 1,
   `doc/user/interface.md`, and `doc/user/hotkeys.md` still describe
   Ctrl+N / **+** as opening a draft request tab without a protocol menu.
   User-doc alignment is [PYPOST-1163](https://pypost.atlassian.net/browse/PYPOST-1163)
   (out of scope). Operator scrape text for `gui_new_tab_actions_total`
   `{source, protocol}` was updated in Step 6
   (`doc/prometheus_monitoring.md`). `doc/dev/` is Step 8.
7. **`open_blank_tab` treats non-WebSocket as HTTP.** Routing is
   `if protocol == TabProtocol.WEBSOCKET: add_blank_websocket_tab()` else
   `add_new_tab()`. Correct for the two-value enum. PYPOST-1165 must add an
   explicit `MCP_CLIENT` branch or a new protocol will silently open HTTP.

## Code Quality Issues

No naming, layering, or architecture-deviation issues that require a 1157
follow-up fix. The implementation matches Option A (`NewTabProtocolPicker`
`QMenu`, HTTP first + `setActiveAction`, `open_blank_tab` as the single
blank-tab router, metrics only after confirm).

Noted for later stories, not for drive-by refactor in this ticket:

| Issue | Location | Notes |
| --- | --- | --- |
| Presenter near LOC cap | `pypost/ui/presenters/tabs_presenter.py` **746 / 785** | Picker lives in `new_tab_protocol_picker.py` as planned. ~39 lines remain. PYPOST-1158 / 1159 / 1165 should keep routing thin or extract further rather than grow this file. |
| Duplicated insert-before-plus | `add_new_tab` and `_insert_websocket_tab` | Same plus-tab insert / `setCurrentWidget` / optional `save_tabs_state` sequence. Extract only if a later story touches both. |
| `_current_tab()` is HTTP-only | `tabs_presenter.py` | Pre-existing; global shortcuts no-op on `WebSocketTab`. Not introduced here. Owned by later WS hotkey / MCP stories ([PYPOST-1162](https://pypost.atlassian.net/browse/PYPOST-1162), [PYPOST-1175](https://pypost.atlassian.net/browse/PYPOST-1175)). |

Hardcoded picker labels (**HTTP Request**, **WebSocket**) match NFR-4 and the
architecture; they are not magic-value debt.

## Missing Tests

**Timeout markers: no BLOCKER.** Every test module added or edited for this
story declares an explicit `pytest.mark.timeout`:

- `tests/test_tabs_presenter.py` — `pytestmark = pytest.mark.timeout(60)`
  (covers `TestHandleNewTabProtocolPicker`, including Step 6 log tests)
- `tests/test_new_tab_protocol_picker.py` — `timeout(60)`
- `tests/test_agent_golden_e2e.py` — `timeout(60)`
- `tests/test_metrics_manager.py` — `timeout(30)`
- `tests/test_metrics_otel.py` — `timeout(30)`

In-scope AC coverage is present: picker before editor, HTTP first/default,
cancel creates no tab and no metric, HTTP confirm → `RequestTab` titled
`New Request`, WebSocket confirm → `WebSocketTab` and not
`open_websocket_tab`, metrics `source` + `protocol`, no MCP Client item,
cancel/confirm INFO logs without payload fields.

Gaps that remain (none are AC breaks):

- **`NewTabProtocolPicker.prompt` is untested.** No test mocks `QMenu.exec`
  to assert HTTP / WebSocket / `None` mapping from action data. Construction
  of order and active action is covered; the `exec` return path is not.
- **No live keyboard/mouse `exec()` test** (intentional shortcut #1).
- **No two-blank-WebSocket uniqueness test** (architecture: blanks must not
  go through saved-profile id dedup). Routing already asserts
  `open_websocket_tab` is not called.
- **No `protocol=http` assertion on Collections **New tab**** — that path
  still defaults to `unknown` (shortcut #5); existing
  `test_track_gui_new_tab_action_collections_context` encodes the current
  contract.

Intentionally not missing for 1157: full WS draft editor tests (PYPOST-1158),
close-last-tab picker tests (PYPOST-1159), MCP Client menu item
(PYPOST-1165).

## Performance Concerns

None for the picker or blank-tab routing. `QMenu.exec` is a short
synchronous GUI wait; tab insertion is the same cost as today's HTTP blank
tab plus one extra `WebSocketTab` widget on the WS path. No new I/O,
handshake, or histogram.

Pre-existing suite risk (not caused by this change):
`tests/test_collections_import_ui.py` can hang in a Qt wait for many minutes
(see Follow-up Tasks). That file was **not** re-run in this step.

## Follow-up Tasks

Phase D of the orchestrator creates Jira issues. Step 7 does not. Items
without a key are left unticketed for Phase D.

1. **NON-BLOCKER — pre-existing / flaky**
   - Node id:
     `tests/test_websocket_client_ui_repro.py::test_presenter_connect_and_disconnect_lifecycle`
   - Symptom: `assert connect_btn.text() == "Disconnect"` with
     `connect_btn.text() == "Connect"`; `HostNotFoundError` on handshake.
   - Evidence (Step 5 / Step 6): failed once in a parallel full `make test`;
     passed isolated on this tree; passed isolated at base `1cc642b2`;
     passed later full suites. Not skipped, xfailed, or deleted.
   - Jira search (`text ~ "test_presenter_connect_and_disconnect_lifecycle"`
     unresolved, and `text ~ "websocket_client_ui_repro"` unresolved): no
     open issue. PYPOST-1132 is Done (original WS client), not this flake.
   - Jira: [PYPOST-1181](https://pypost.atlassian.net/browse/PYPOST-1181)

2. **NON-BLOCKER — pre-existing hang**
   - File: `tests/test_collections_import_ui.py` (module
     `pytestmark = pytest.mark.timeout(60)`; body uses `_IMPORT_WAIT_MS = 5000`
     with `process_until`).
   - Symptom: during Step 6 `make test`, stuck in a Qt wait ~10 minutes.
     Three isolated `make test PYTEST_ARGS='tests/test_collections_import_ui.py'`
     runs were terminated (~4m, ~2m, ~2m) with no tests finishing.
   - Out of scope for PYPOST-1157. Do not skip, xfail, or delete. This step
     did not re-run that file.
   - Jira search (`text ~ "test_collections_import_ui"` unresolved): no
     open issue.
   - Jira: [PYPOST-1182](https://pypost.atlassian.net/browse/PYPOST-1182)

3. **NON-BLOCKER — pre-existing / flaky**
   - Node id:
     `tests/test_mcp_server_manager.py::test_update_tools_restarts_when_exposed_set_changes`
   - Symptom: `EADDRINUSE` after MCP server restart. Did not reproduce in
     later PYPOST-1157 suite runs.
   - Jira: [PYPOST-1178](https://pypost.atlassian.net/browse/PYPOST-1178)

4. **NON-BLOCKER — intentional epic scope (not incomplete 1157 work)**
   - Placeholder `WebSocketTab` / draft restore exclusion / full draft
     editor: Jira: [PYPOST-1158](https://pypost.atlassian.net/browse/PYPOST-1158)
   - MCP Client picker item and `protocol=mcp_client`:
     Jira: [PYPOST-1165](https://pypost.atlassian.net/browse/PYPOST-1165)

5. **NON-BLOCKER — intentional epic scope**
   - Close-last-tab / empty-workspace fallback still HTTP-only
     (`add_new_tab`, not `handle_new_tab` / `open_blank_tab`).
   - Jira: [PYPOST-1159](https://pypost.atlassian.net/browse/PYPOST-1159)

6. **NON-BLOCKER — metrics completeness**
   - Collections **New tab** increments
     `gui_new_tab_actions_total{source="collections_context",protocol="unknown"}`
     even though the tab is always HTTP. Pass `protocol="http"` (or the real
     item protocol) when a later collections story touches that path
     ([PYPOST-1160](https://pypost.atlassian.net/browse/PYPOST-1160)).
   - Unticketed as a dedicated Debt issue; can ride on PYPOST-1160.

7. **NON-BLOCKER — test gap**
   - Unit-test `NewTabProtocolPicker.prompt` with a mocked `QMenu.exec`
     (HTTP, WebSocket, `None`) so action-data mapping is covered without a
     live popup. Do not add a real `exec()` hang in CI.
   - Jira: [PYPOST-1180](https://pypost.atlassian.net/browse/PYPOST-1180)

8. **NON-BLOCKER — user docs**
   - `doc/user/websocket.md` step 1 still says “select the **WebSocket**
     mode”; `doc/user/interface.md` / `hotkeys.md` still omit the picker.
   - Jira: [PYPOST-1163](https://pypost.atlassian.net/browse/PYPOST-1163)

9. **NON-BLOCKER — capacity**
   - Keep `tabs_presenter.py` under 785 LOC in PYPOST-1158 / 1159 / 1165
     (currently 746). Observation only; no new ticket.
