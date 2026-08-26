# PYPOST-1166: Technical Debt Analysis

PYPOST-1166 (MCP-TM-2) filled the PYPOST-1165 stub with a blank MCP Client
draft shell: URL bar, Connect / Disconnect, disconnected state, empty tool
browser, draft omission from `save_tabs_state`, and `close_tab` →
`presenter.teardown()`. There is **no AC-breaking debt** in this story's
own change. Remaining items are intentional later MCP-TM work, presenter
LOC headroom, a few untested chrome edges, and pre-existing gaps from
PYPOST-1165. None of those items block Step 8.

Jira keys below that already exist are cited for context. **New follow-up
issues are not created in this step** (Phase D / orchestrator). Unticketed
items say `Jira: none`.

## Shortcuts Taken

1. **Connect is local chrome, not live MCP.** `McpClientPresenter.connect_requested`
   sets `_session = object()`, flips state to `CONNECTED`, and never calls
   `MCPClientService`. Disconnect / teardown drop that holder and return to
   `DISCONNECTED`. Architecture Option A and FR-2 required usable chrome;
   live initialize, `list_tools`, and connect-failure UI are MCP-TM-3.
2. **`CONNECTING` is reserved and unused.** `McpClientSessionState.CONNECTING`
   exists on the enum and badge map so MCP-TM-3 can show in-flight initialize
   without a new state type. This story never enters that state.
3. **Empty URL still "connects" locally.** There is no URL validation and no
   error surface. Architecture Q&A: keep Disconnected or apply local
   Connected; this implementation applies local Connected. TM-3 owns
   validation and errors.
4. **Draft UUID exists in memory but is never written to `open_tabs`.**
   Stronger than WebSocket write-then-miss. First save / saved-profile
   restore is MCP-TM-7 (out of this story). Until then every blank MCP
   Client tab is a draft.
5. **Duck-typed `close_tab` teardown.** `getattr(tab, "presenter")` then
   `teardown` if callable, covering WebSocket and MCP Client without a
   second `isinstance` branch. A tab with a non-teardown presenter is
   silently skipped (same as before for widgets without a presenter).
6. **Close-last-tab fallback stays HTTP-only.** `close_tab` still calls
   `add_new_tab(save_state=False)` when `_request_tab_count() == 0`.
   Production count includes `McpClientTab`, so an MCP-only strip is not
   treated as empty. Empty-workspace picker is
   [PYPOST-1159](https://pypost.atlassian.net/browse/PYPOST-1159).
7. **User-facing docs not rewritten here.** MCP Client draft chrome in
   `doc/user/` is
   [PYPOST-1168](https://pypost.atlassian.net/browse/PYPOST-1168).
   `doc/dev/` for this shell is Step 8 of this task.

## Code Quality Issues

Implementation matches architecture: fill `McpClientTab` +
`McpClientPresenter`; chrome in `connection_bar.py` / `tool_browser.py`;
thin factory in `TabsPresenter`; no `MCPClientService`.

- **Presenter LOC headroom** — `tabs_presenter.py` **771 / 785** (snapshot
  `ai-tasks/PYPOST-376/baseline-metrics.md`). **~14 lines** remain (was
  ~20 after 1165). Factory + duck-typed teardown fit. Later MCP-TM work
  that needs restore / env / `_current_tab` wiring must extract shared
  insert-before-plus **before** growing this file. Do not put URL /
  Connect / tools here.
- **Triplicated insert-before-plus** — `add_new_tab`,
  `_insert_websocket_tab`, `add_blank_mcp_client_tab` share plus-tab
  insert / `setCurrentWidget` / optional `save_tabs_state`. Extract when
  the next story cannot fit in the 14-line remainder.
- **`_current_tab()` is HTTP-only** — pre-existing; global shortcuts
  no-op on `WebSocketTab` and `McpClientTab`. Not a 1166 defect. Later
  editor / hotkey stories own this
  ([PYPOST-1162](https://pypost.atlassian.net/browse/PYPOST-1162)).
- **Env snapshot not pushed to MCP tabs** —
  `on_env_variables_changed` / `on_env_hidden_keys_changed` cover HTTP
  and WebSocket only. Headers / `{{ vars }}` are MCP-TM-5.
- **Dummy session holder** — `mcp_client_presenter.py` uses
  `_session = object()` so teardown has something to release. Replace
  with a real session in MCP-TM-3.
- **Dual URL write** — `McpClientTab._on_url_changed` and
  `connect_requested` → `_sync_url_from_tab`. Harmless duplication; keep
  one path when TM-3 edits the presenter.
- **Connect / Disconnect stay enabled in both states** —
  `connection_bar.py` does not disable-when-connected. Fine for chrome;
  TM-3 may gate buttons during `CONNECTING`.
- **Widget id on inner list** — `MCP_CLIENT_TOOL_BROWSER` is on the inner
  `QListWidget`, not the wrapper. Tests `findChild` that widget. Do not
  move the id onto the wrapper without updating tests.
- **Test helper still HTTP-only** — `tests/test_tabs_presenter.py`
  `_request_tab_count` counts `RequestTab` only. Production includes
  `WebSocketTab` and `McpClientTab`. Carried from 1165.

Hardcoded labels (**Connect**, **Disconnect**, **Disconnected**, **New MCP
Client**, **Remote tools**) and URL placeholder
`http://127.0.0.1:1080/mcp` match NFR-3 / architecture; they are not
magic-value debt.

## Missing Tests

**Timeout markers: no BLOCKER.** Modules added or edited for this story
already declare explicit `pytest.mark.timeout`:

- `tests/test_mcp_client_tab.py` — `timeout(30)`
- `tests/test_tabs_presenter.py` — `timeout(60)`

In-scope AC coverage is present: draft factory (title, empty URL, name),
`save_tabs_state` omits draft id and restore does not create
`McpClientTab`, `close_tab` calls `teardown`, chrome (URL, Connect,
Disconnect, disconnected state, empty tool list, not HTTP `METHOD_COMBO`),
caplog for connect / disconnect / teardown without URL dumps.

Gaps that remain (none are AC breaks):

- **No click-Connect UI test.** Architecture listed an optional click that
  updates local state without calling `MCPClientService`. Presenter logging
  test calls `connect_requested` directly. No test that the button slot
  sets `CONNECTED` or that `MCPClientService.run` is not invoked.
- **No close-last-tab / production-count test for MCP Client.** Closing
  the last HTTP tab while an MCP Client tab remains must not call
  `add_new_tab`. Test helper still counts `RequestTab` only. Tracked by
  [PYPOST-1183](https://pypost.atlassian.net/browse/PYPOST-1183)
  (from PYPOST-1165). Optional construction-only `test_mcp_client_tab.py`
  now exists; remaining 1183 work is presenter count / last-tab.
- **No test that Connect with empty URL is allowed.** Matches current
  product choice; add when TM-3 adds validation.

Intentionally not missing for 1166: live `list_tools`, invoke, headers,
Collections save, outbound operation counters, user-doc tests.

## Performance Concerns

None for the draft shell. Connect / Disconnect / teardown are synchronous
GUI work; `_session = object()` is not a network client. No new Prometheus
histograms (architecture forbade `mcp_client_connect_total` here).

`tabs_presenter.py` at **771 / 785** is a capacity risk for the next
stories that must touch the presenter, not a runtime performance issue.

## Follow-up Tasks

Phase D of the orchestrator creates Jira issues. Step 7 does not, except
citing stories that already exist.

1. **NON-BLOCKER — intentional epic scope (not incomplete 1166 work)**
   - Replace local Connect with initialize + `list_tools`; populate the
     existing tool browser; surface connect errors; use `CONNECTING`;
     replace `_session = object()` with a real outbound holder.
     Outbound `connect` / `list_tools` counters belong here.
   - Verdict: **NON-BLOCKER** (AC: chrome usable; live protocol is TM-3).
   - Jira: [PYPOST-1169](https://pypost.atlassian.net/browse/PYPOST-1169)

2. **NON-BLOCKER — intentional epic scope**
   - Interactive `call_tool`, schema forms, result pane.
   - Verdict: **NON-BLOCKER**.
   - Jira: [PYPOST-1170](https://pypost.atlassian.net/browse/PYPOST-1170)

3. **NON-BLOCKER — intentional epic scope**
   - Headers table, `{{ var }}` resolution, env push into the MCP Client
     tab / presenter (`on_env_variables_changed` today skips
     `McpClientTab`).
   - Verdict: **NON-BLOCKER**.
   - Jira: [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167)

4. **NON-BLOCKER — user docs**
   - `doc/user/` still describes Ctrl+N / **+** without the MCP Client
     draft shell (URL, Connect / Disconnect, empty tools).
   - Verdict: **NON-BLOCKER**.
   - Jira: [PYPOST-1168](https://pypost.atlassian.net/browse/PYPOST-1168)

5. **NON-BLOCKER — test gap (already ticketed)**
   - Align `tests/test_tabs_presenter.py` `_request_tab_count` with
     production `(RequestTab, WebSocketTab, McpClientTab)`.
   - Closing the last HTTP tab while an MCP Client tab remains must not
     call `add_new_tab`.
   - Construction-only chrome module exists (`test_mcp_client_tab.py`);
     remaining work is presenter count / last-tab.
   - Verdict: **NON-BLOCKER**.
   - Jira: [PYPOST-1183](https://pypost.atlassian.net/browse/PYPOST-1183)

6. **NON-BLOCKER — capacity**
   - `tabs_presenter.py` is **771 / 785** (~14 LOC). Before MCP-TM-3 /
     MCP-TM-5 / MCP-TM-7 add restore, env, or extra factory lines,
     extract shared insert-before-plus used by HTTP / WS / MCP factories.
   - Verdict: **NON-BLOCKER**.
   - Jira: [PYPOST-1184](https://pypost.atlassian.net/browse/PYPOST-1184)

7. **NON-BLOCKER — test gap (ticket later)**
   - Optional: click **Connect** updates badge to Connected; patch
     `MCPClientService` and assert `run` is not called; Disconnect
     returns Disconnected. Keep `pytestmark` timeout; no network.
   - Verdict: **NON-BLOCKER**.
   - Jira: [PYPOST-1185](https://pypost.atlassian.net/browse/PYPOST-1185)

8. **NON-BLOCKER — Step 8 of this task (not a new ticket)**
   - Update `doc/dev/` for the MCP Client draft shell: `McpClientTab` /
     presenter, draft omission, duck-typed teardown, widget ids.
   - Owned by PYPOST-1166 Step 8.
   - Jira: none
