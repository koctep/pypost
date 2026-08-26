# PYPOST-1165: Technical Debt Analysis

PYPOST-1165 (MCP-TM-1) shipped the third picker item **MCP Client**,
`TabProtocol.MCP_CLIENT = "mcp_client"`, an explicit `open_blank_tab` branch,
stub `McpClientTab`, and `gui_new_tab_actions_total` allow-list
`mcp_client`. There is **no AC-breaking debt** in this story's own change.
Remaining items are the intentional stub vs
[PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166) draft shell,
presenter LOC headroom, a few untested stub lifecycle edges, and
pre-existing suite instability found during Step 4. None of those items
block Step 8.

Jira keys below that already exist are cited for context. **New follow-up
issues are not created in this step** (Phase D / orchestrator). Unticketed
items say `Jira: none`.

## Shortcuts Taken

1. **`McpClientTab` is a placeholder, not the draft shell.** Confirming
   **MCP Client** opens a dedicated `QWidget` with an empty layout, inner
   `QLabel("MCP Client")`, widget id `MCP_CLIENT_TAB_PAGE`, and tab title
   `"New MCP Client"`. Constructor takes only `parent`. There is no URL
   bar, Connect / Disconnect, connection state, tool browser,
   `McpClientPresenter`, or `McpClientConnection`. Architecture
   (placeholder specification / FR-4.3) required this split. PYPOST-1166
   **replaces stub contents inside the same class**. Do not treat the
   missing chrome as incomplete 1165 work.
2. **Stub is omitted from session persist / restore.** `save_tabs_state`
   still writes only `RequestTab` ids and `WebSocketTab.connection_data.id`.
   `restore_tabs` has no MCP branch. Architecture listed this as
   acceptable; draft restore rules belong to PYPOST-1166. Closing the
   app with only an MCP stub open will restore as a blank HTTP tab (same
   empty-workspace path as today).
3. **`open_blank_tab` still falls through to HTTP for unknown values.**
   Routing is now `WEBSOCKET` → `MCP_CLIENT` → `add_new_tab()`. The 1157
   else-HTTP trap is closed for `TabProtocol.MCP_CLIENT`. A *future*
   fourth enum value without a new branch would still open HTTP. Keep
   adding explicit branches (or a dispatch map) when the next protocol
   lands.
4. **Injectable picker instead of live `QMenu.exec()` in tests.** Unchanged
   from PYPOST-1157. Presenter tests inject `TabProtocol.MCP_CLIENT`.
   Picker tests mock `menu.exec` only for the MCP confirm mapping. CI
   never exercises the live three-item popup, Enter-to-confirm HTTP, or
   Esc/click-away.
5. **Close-last-tab / empty-workspace fallback stays HTTP-only.**
   `close_tab` still calls `add_new_tab(save_state=False)` when
   `_request_tab_count() == 0`. Architecture / FR out of scope;
   [PYPOST-1159](https://pypost.atlassian.net/browse/PYPOST-1159). This
   story only added `McpClientTab` to the count tuple so an MCP-only
   strip is not treated as empty.
6. **User-facing picker copy not rewritten here.** Three-item user docs
   are [PYPOST-1168](https://pypost.atlassian.net/browse/PYPOST-1168).
   Operator scrape text already lists `mcp_client`
   (`doc/prometheus_monitoring.md`, Step 6). `doc/dev/` picker docs stay
   Step 8 (`doc/dev/new_tab_protocol_picker.md` still describes two
   items).

## Code Quality Issues

Implementation matches architecture Option A: same
`NewTabProtocolPicker`, HTTP first + `setActiveAction` +
`exec(..., http_action)`, named stub module, thin presenter factory,
metrics allow-list.

| Issue | Location | Notes |
| --- | --- | --- |
| Presenter LOC headroom | `pypost/ui/presenters/tabs_presenter.py` **765 / 785** | Architecture projected ~765. **~20 lines** remain. PYPOST-1166 must put URL / Connect / tools in `mcp_client_tab.py` (and a presenter module if needed), not grow this file. If restore / env / `_current_tab` wiring cannot fit, extract a shared insert-before-plus helper first. |
| Triplicated insert-before-plus | `add_new_tab`, `_insert_websocket_tab`, `add_blank_mcp_client_tab` | Same plus-tab insert / `setCurrentWidget` / optional `save_tabs_state` sequence. Extract when the next story touches two of the three factories. |
| `_current_tab()` is HTTP-only | `tabs_presenter.py` | Pre-existing; global shortcuts no-op on `WebSocketTab` and now on `McpClientTab`. Not introduced as a 1165 defect. Later editor / hotkey stories own this ([PYPOST-1162](https://pypost.atlassian.net/browse/PYPOST-1162), [PYPOST-1175](https://pypost.atlassian.net/browse/PYPOST-1175), PYPOST-1166). |
| Overlapping picker tests | `tests/test_new_tab_protocol_picker.py` | `test_build_menu_http_request_is_first_default` and `test_build_menu_includes_mcp_client_as_third_item` both assert the three labels and HTTP as `activeAction`. The third-item test is a superset (also asserts third `data()`). Harmless duplication; fold when that file is next edited. |
| Test helper still HTTP-only | `tests/test_tabs_presenter.py` `_request_tab_count` | Counts `RequestTab` only. Production `_request_tab_count` includes `WebSocketTab` and `McpClientTab`. The helper cannot catch a regression that drops the stub from the production count. |

Hardcoded labels (**HTTP Request**, **WebSocket**, **MCP Client**) and
title `"New MCP Client"` match NFR-4 / architecture; they are not
magic-value debt.

## Missing Tests

**Timeout markers: no BLOCKER.** Modules added or edited for this story
already declare explicit `pytest.mark.timeout`:

- `tests/test_tabs_presenter.py` — `timeout(60)`
- `tests/test_new_tab_protocol_picker.py` — `timeout(60)`
- `tests/test_metrics_manager.py` — `timeout(30)`
- `tests/test_metrics_otel.py` — `timeout(30)`
- `tests/test_metrics_registry.py` — existing module marker

In-scope AC coverage is present: three-item menu, HTTP first/default,
`prompt()` maps MCP Client (mocked `exec`), confirm is `McpClientTab`
not HTTP/WebSocket, `open_blank_tab` does not call `add_new_tab`,
metrics `protocol=mcp_client` (Prometheus scrape + OTel), HTTP confirm
and cancel regression from PYPOST-1157.

Gaps that remain (none are AC breaks):

- **No close-last-tab / count test for the stub.** Architecture required
  `McpClientTab` in `_request_tab_count` so closing the last HTTP tab
  while an MCP stub is open does **not** auto-open HTTP. Production
  includes the type; no test closes HTTP leaving only `McpClientTab`,
  or asserts production count after `add_blank_mcp_client_tab`.
- **No stub chrome unit test.** Nothing asserts widget id
  `pypost_mcp_client_tab_page`, tab strip title `"New MCP Client"`, or
  constructor-only `McpClientTab(parent=None)` without a presenter.
  Presenter tests only check `isinstance(..., McpClientTab)`.
- **`prompt()` HTTP / WebSocket / `None` mapping still thin.** MCP
  confirm is covered. HTTP / cancel `exec` return paths remain
  [PYPOST-1180](https://pypost.atlassian.net/browse/PYPOST-1180)
  (pre-existing 1157 gap). Do not add a live `exec()` hang in CI.
- **No `save_tabs_state` omission test** for the stub (architecture:
  need not persist). Add when PYPOST-1166 defines restore rules.

Intentionally not missing for 1165: URL / Connect / tool-browser tests
(PYPOST-1166), close-last-tab picker (PYPOST-1159), outbound
`connect` / `list_tools` / `call_tool` counters, user-doc tests.

## Performance Concerns

None for the picker or stub. `QMenu.exec` is a short synchronous GUI
wait; inserting `McpClientTab` is one extra empty `QWidget` plus a
label. No MCP SDK, network, or new histograms.

Pre-existing suite risk (not caused by this change):
`tests/test_agent_dialog_settle_e2e.py` segfaulted once during Step 4
full `make test` (exit -11) and passed on re-run. Tracked by
[PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115). See
Follow-up Tasks.

## Follow-up Tasks

Phase D of the orchestrator creates Jira issues. Step 7 does not.

1. **NON-BLOCKER — intentional epic scope (not incomplete 1165 work)**
   - Replace stub contents inside `McpClientTab` with the draft shell:
     URL bar, Connect / Disconnect, connection state, empty tool
     browser, draft restore exclusion. Keep the class name, package
     `pypost.ui.widgets.mcp_client`, widget id, and picker item.
   - Do not grow `tabs_presenter.py` past **785** LOC (now **765**).
   - Jira: [PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166)

2. **NON-BLOCKER — test gap (ticket later)**
   - Add presenter tests:
     - After `open_blank_tab(MCP_CLIENT)`, tab text is `"New MCP Client"`
       and `objectName` / widget id is `pypost_mcp_client_tab_page`.
     - With only `McpClientTab` open (close any HTTP),
       `close_tab` on that stub is the last-tab case **or** closing the
       last HTTP while an MCP stub remains must **not** call
       `add_new_tab`. Align the test helper with production
       `(RequestTab, WebSocketTab, McpClientTab)` so the count cannot
       silently ignore the stub.
   - Optional: `tests/test_mcp_client_tab.py` construction-only
     (`pytestmark` timeout 30 or 60), no MCP SDK.
   - Jira: [PYPOST-1183](https://pypost.atlassian.net/browse/PYPOST-1183)

3. **NON-BLOCKER — capacity**
   - Before PYPOST-1166 adds restore / env / teardown to the presenter,
     extract shared insert-before-plus used by HTTP / WS / MCP factories
     so `tabs_presenter.py` stays under 785 (20-line headroom).
   - Observation for 1166; no dedicated Debt ticket unless that story
     cannot fit.
   - Jira: none

4. **NON-BLOCKER — pre-existing / flaky**
   - Node id: `tests/test_agent_dialog_settle_e2e.py` (module; Step 4
     full `make test` exited **-11** / SIGSEGV once, then passed on
     re-run). Unrelated to picker / stub code.
   - Verdict: **NON-BLOCKER — pre-existing**. Do not skip, xfail, or
     delete.
   - Jira: [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115)

5. **NON-BLOCKER — intentional epic scope**
   - Close-last-tab / empty-workspace fallback still HTTP-only.
   - Jira: [PYPOST-1159](https://pypost.atlassian.net/browse/PYPOST-1159)

6. **NON-BLOCKER — user docs**
   - `doc/user/` still describes Ctrl+N / **+** without **MCP Client**.
   - Jira: [PYPOST-1168](https://pypost.atlassian.net/browse/PYPOST-1168)

7. **NON-BLOCKER — pre-existing test gap**
   - Unit-test `NewTabProtocolPicker.prompt` with mocked `QMenu.exec`
     for HTTP, WebSocket, and `None` (MCP mapping already exists).
   - Jira: [PYPOST-1180](https://pypost.atlassian.net/browse/PYPOST-1180)

8. **NON-BLOCKER — Step 8 of this task (not a new ticket)**
   - Update `doc/dev/new_tab_protocol_picker.md` from two-item menu /
     "MCP Client is missing" to three items, `mcp_client` metrics, and
     stub confirm → `McpClientTab`. Owned by PYPOST-1165 Step 8.
