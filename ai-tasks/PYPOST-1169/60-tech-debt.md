# PYPOST-1169: Technical Debt Analysis

PYPOST-1169 (MCP-TM-3) made MCP Client Connect / Refresh a real outbound
`list_tools`: GUI-thread `resolve_outbound_fields`, presenter-owned
`McpClientOutboundWorker` calling `MCPClientService.run` with resolved
url/headers, name/description in `McpClientToolBrowser`, distinct Connect
vs Refresh error policy, and outbound counters
`mcp_client_connect_total` / `mcp_client_list_tools_total`.

There is **no AC-breaking debt** in this story's change. Remaining items
are intentional later MCP-TM work, presenter LOC headroom, deferred
factory metrics wiring, and a few untested edges. None of those items
block Step 8.

Jira keys below that already exist are cited for context. **New follow-up
issues are not created in this step** (Phase D / orchestrator). Already
linked keys used here:
[PYPOST-1170](https://pypost.atlassian.net/browse/PYPOST-1170),
[PYPOST-1184](https://pypost.atlassian.net/browse/PYPOST-1184),
[PYPOST-1186](https://pypost.atlassian.net/browse/PYPOST-1186),
[PYPOST-1187](https://pypost.atlassian.net/browse/PYPOST-1187),
[PYPOST-1188](https://pypost.atlassian.net/browse/PYPOST-1188).

## Shortcuts Taken

1. **Factory does not inject `metrics=`.** `McpClientPresenter` accepts
   optional `metrics=` and tests pass a `MetricsRegistry`.
   `add_blank_mcp_client_tab` still constructs the presenter with only
   `env_vars` / `hidden_keys`. Passing `metrics=self._metrics` would add
   a line to `tabs_presenter.py` (779 / 785). This story made **zero**
   edits to that file. Live `/metrics` scrape for Connect / Refresh in
   the running app therefore waits on factory injection **after**
   PYPOST-1184 extract (or any later story that can spend a factory
   line).
2. **Connect / Refresh do not call `execute_outbound`.** Architecture
   Option A: resolve on the GUI thread, then worker `run` with captured
   fields. Sync `execute_outbound` remains for tests and MCP-TM-4
   invoke. The header contract is the same; the method body is not
   reused on `QThread`.
3. **Chrome “session” is still `_session = object()`.** Success sets a
   dummy holder so teardown / Disconnect have something to drop.
   `MCPClientService.run` still opens and closes Streamable HTTP per
   call. A held `ClientSession` is MCP-TM-4
   ([PYPOST-1170](https://pypost.atlassian.net/browse/PYPOST-1170)).
4. **First `tools/list` page only.** `nextCursor` is ignored. Matches
   existing `MCPClientService`. Pagination is out of this story.
5. **No `inputSchema` on list items.** Rows are `(name, description)`
   only. Schema-guided forms belong to PYPOST-1170.
6. **Disconnect does not `requestInterruption` on the worker.**
   Generation is bumped so late results are ignored; `_drop_worker`
   disconnects signals and `deleteLater`. A still-running `anyio.run`
   may finish in the background until the 25s service timeout.
7. **User-facing docs not rewritten here.** MCP-TM-8. `doc/dev/` for
   live Connect / Refresh is Step 8 of this task.
8. **Dirty inbound `mcp_server.py` left alone.** Unrelated to outbound
   discovery.

## Code Quality Issues

Implementation matches architecture: Connect / Refresh / worker / error
chrome live in `McpClientPresenter` and `mcp_client` widgets;
`tabs_presenter.py` stays a thin factory at **779 / 785**.

- **Presenter LOC is still tight — `tabs_presenter.py` 779 / 785.** This
  story spent **zero** of the remaining six lines. Factory metrics
  injection is deferred for that reason (see Shortcuts). MCP-TM-4 /
  MCP-TM-7 must extract shared insert-before-plus **before** adding
  restore or extra factory kwargs. Already ticketed as PYPOST-1184
  (ticket text may still cite 771/785 from PYPOST-1166).
- **Dummy session holder remains.** `_session = object()` after
  successful discovery. Replace with a real outbound session in
  PYPOST-1170; do not invent a second holder here.
- **`execute_outbound` is still GUI-thread / blocking.** Fine for
  unit tests. Interactive `call_tool` must use the worker (or a session
  holder) so invoke does not freeze the window.
- **Triplicated Key/Value tables** — unchanged from PYPOST-1167.
  `McpClientHeadersTable` is still a copy. Already ticketed as
  PYPOST-1186.
- **Duplicate URL / headers write** — tab slots write
  `connection_data`; presenter `_sync_fields_from_tab` copies again
  before resolve. Harmless; keep one path if TM-4 edits the presenter.
- **Dict last-wins on duplicate header names.** Same as HTTP Headers
  tables.
- **Duck-typed env fan-out** — unchanged; tabs without
  `set_variables` / `set_hidden_keys` are skipped.

Hardcoded copy (**Refresh**, **Refreshing tools...**, **Enter a server
URL.**, **MCP server returned an invalid tools list.**) matches
architecture; they are not magic-value debt.

## Missing Tests

**Timeout markers: no BLOCKER.** Modules added or edited for this story
already declare explicit `pytest.mark.timeout`:

- `tests/test_mcp_client_tab.py` — `timeout(30)`
- `tests/test_mcp_client_presenter.py` — `timeout(10)`
- `tests/test_tabs_presenter.py` — `timeout(60)`
- `tests/test_metrics_registry.py` — `timeout(30)`
- `tests/test_metrics_otel.py` — `timeout(30)`

In-scope AC coverage is present: Connect fills name/description;
empty-URL and `ExecutionError` Connect fail (not connected, empty
tools); Refresh fail stays connected with stale list; resolved URL /
headers forwarded into `run`; Connect / Refresh counters; secret-safe
logs (no URL, no `headers` substring).

Gaps that remain (none are AC breaks):

- **No live Streamable HTTP integration test.** GUI tests mock
  `MCPClientService.run`. Optional later; not required for MCP-TM-3 AC.
- **No GUI test that types Headers-table rows then Connect.**
  `test_connect_forwards_resolved_url_and_headers` seeds
  `McpClientConnection.headers` on construct. Widget →
  `_sync_fields_from_tab` → `run` is still the PYPOST-1187 gap.
- **No pagination / `nextCursor` test.** Out of scope (first page
  only).
- **No factory scrape test that blank MCP tabs increment
  `mcp_client_*` on `/metrics`.** Counters work when `metrics=` is
  injected; the running factory does not inject yet.

Intentionally not missing for 1169: invoke UI; schema forms; Collections
persist; inbound **MCP Servers…**; Ctrl+H on MCP Client.

## Performance Concerns

Each Connect / Refresh is one-shot initialize + `list_tools` + close
(up to `MCP_TOTAL_TIMEOUT` 25s on the worker). That is acceptable for
discovery. Holding a session for invoke is PYPOST-1170, not a runtime
bug in this story.

`tabs_presenter.py` at **779 / 785** is a **capacity** risk for factory
metrics injection and later stories, not a runtime performance issue.

No Grafana dashboards or alerting rules were added (Step 6).

## Follow-up Tasks

Phase D of the orchestrator creates Jira issues. Step 7 does not.
Existing keys are cited; nothing new is filed here.

1. **NON-BLOCKER — intentional epic scope (not incomplete 1169 work)**
   - Interactive `call_tool`, schema-guided argument forms, and result
     pane. May add a held `ClientSession`. Must keep the same
     header-aware outbound path (GUI resolve, not Qt on the worker).
     Do not run long `execute_outbound` on the GUI thread.
   - Verdict: **NON-BLOCKER**.
   - Jira: [PYPOST-1170](https://pypost.atlassian.net/browse/PYPOST-1170)

2. **NON-BLOCKER — capacity (already ticketed; still 779 / 785)**
   - Extract shared insert-before-plus used by HTTP / WS / MCP
     factories. **Then** pass `metrics=self._metrics` into
     `McpClientPresenter` so live Connect / Refresh hit Prometheus.
     Factory injection is deferred **because** this file is 779 / 785
     and this story must not grow it.
   - Verdict: **NON-BLOCKER**.
   - Jira: [PYPOST-1184](https://pypost.atlassian.net/browse/PYPOST-1184)

3. **NON-BLOCKER — shared Key/Value table (still relevant)**
   - Extract one empty-row `VariableAwareTableWidget` used by HTTP,
     WebSocket handshake, and MCP Client Headers. This story did not
     change the headers table.
   - Verdict: **NON-BLOCKER**.
   - Jira: [PYPOST-1186](https://pypost.atlassian.net/browse/PYPOST-1186)

4. **NON-BLOCKER — test gap (still relevant)**
   - Optional: GUI test that edits the Headers table then Connect /
     `execute_outbound` asserts `run(..., headers=)` from **widget**
     data; optional hover / hidden-key `********` on
     `pypost_mcp_client_headers_table`. Keep `pytestmark` timeout; no
     network. Live Connect now covers fixture-seeded headers; table
     typing is still uncovered.
   - Verdict: **NON-BLOCKER**.
   - Jira: [PYPOST-1187](https://pypost.atlassian.net/browse/PYPOST-1187)

5. **NON-BLOCKER — pre-existing/flaky (still relevant; not re-run here)**
   - Node id:
     `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises`
   - Repro: parallel `make test`; suspected Qt `apply_theme` vs uvicorn
     import race. Isolated file run passed on PYPOST-1167. Unrelated to
     live Connect assertions.
   - Verdict: **NON-BLOCKER — pre-existing**.
   - Jira: [PYPOST-1188](https://pypost.atlassian.net/browse/PYPOST-1188)

6. **NON-BLOCKER — Step 8 of this task (not a new ticket)**
   - Update `doc/dev/` for live Connect / Refresh: worker vs
     `execute_outbound`, Connect vs Refresh chrome, outbound counters
     vs inbound `mcp_requests_received_total`, factory metrics
     injection deferred at 779 / 785.
   - Owned by PYPOST-1169 Step 8.
   - Jira: none
