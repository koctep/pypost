# PYPOST-1167: Technical Debt Analysis

PYPOST-1167 (MCP-TM-5) added connection headers and environment templating
to the MCP Client draft: `McpClientHeadersTable` on tab chrome, URL
`VariableAwareLineEdit`, `McpClientPresenter.resolve_outbound_fields` /
`execute_outbound` into existing `MCPClientService.run(..., headers=)`,
and duck-typed env fan-out in `TabsPresenter`. HTTP method **MCP** header
forwarding stays the PYPOST-1173 regression gate (not re-wired here).

There is **no AC-breaking debt** in this story's own change. Remaining
items are intentional later MCP-TM work, presenter LOC headroom, a copied
headers table, and a few untested edges. None of those items block Step 8.

Jira keys below that already exist are cited for context. **New follow-up
issues are not created in this step** (Phase D / orchestrator). Unticketed
items say `Jira: none`. Already-linked keys used here:
[PYPOST-1169](https://pypost.atlassian.net/browse/PYPOST-1169),
[PYPOST-1170](https://pypost.atlassian.net/browse/PYPOST-1170),
[PYPOST-1184](https://pypost.atlassian.net/browse/PYPOST-1184).

## Shortcuts Taken

1. **Connect still does not call `execute_outbound`.** `connect_requested`
   remains local chrome (`_session = object()`, `CONNECTED`) and never
   resolves or sends headers. Architecture Option A: FR-3 is the
   `execute_outbound` contract; live initialize / `list_tools` is MCP-TM-3
   and **must** call that path so auth cannot be skipped.
2. **Headers table is a copy, not a shared widget.** Architecture rejected
   importing nested `RequestEditor.KeyValueTable` and
   `WebSocketKeyValueTable`. `McpClientHeadersTable` duplicates empty-row
   Key/Value behavior on `VariableAwareTableWidget`. Extracting a shared
   table was explicitly out of this story.
3. **Header rows are in-memory on the draft only.**
   `McpClientConnection.headers` is not on `Collection`. Persistence is
   MCP-TM-7 (out of this story).
4. **Unresolved `{{ }}` is left as text.** Same HTTP / method-MCP rule;
   `resolve_proxy_headers` (fail-fast) was not used. Missing env vars do
   not error on MCP Client send.
5. **Lazy `MCPClientService` import.** `_client()` imports the service on
   first `execute_outbound` when no `mcp_client=` was injected. Avoids
   pulling Streamable HTTP / SDK into draft-chrome construction. MCP-TM-3
   can keep injecting a client or worker.
6. **Ctrl+H is not wired to MCP Client Headers.** NFR-5: HTTP
   `handle_switch_to_headers_global` still assumes `RequestTab`. Do not
   grow that handler in this file.
7. **User-facing docs not rewritten here.** MCP Client headers /
   templating in `doc/user/` belong to the user-docs story. `doc/dev/`
   for this wiring is Step 8 of this task.
8. **Dirty inbound `mcp_server.py` left alone.** Bind-wait / port retry
   is not outbound client headers. Mixing it in would be unrelated scope.

## Code Quality Issues

Implementation matches architecture: headers UI on `McpClientTab`;
presenter owns resolve + `execute_outbound`; `MCPClientService` and
`RequestService._execute_mcp` unchanged; `tabs_presenter.py` stays a thin
factory.

- **Presenter LOC is tight — `tabs_presenter.py` 779 / 785.** Snapshot
  `ai-tasks/PYPOST-376/baseline-metrics.md`. This story used **8 of the
  remaining 14 lines** (factory `env_vars` / `hidden_keys` kwargs +
  duck-typed `set_variables` / `set_hidden_keys`). **Six lines** remain.
  Cosmetic wraps of the `getattr` fan-out were skipped so the file stays
  off the PYPOST-376 cap. MCP-TM-3 / MCP-TM-4 / MCP-TM-7 must extract
  shared insert-before-plus **before** adding restore or extra factory
  lines. Do not put headers UI, template loops, or Ctrl+H routing in
  this file. Already ticketed as PYPOST-1184 (description still says
  771/785; current count is 779/785).
- **Triplicated Key/Value tables** — HTTP `KeyValueTable`,
  `WebSocketKeyValueTable`, and `McpClientHeadersTable` share empty-row
  + `get_data` / `set_data`. Acceptable copy for this story; a shared
  widget is later cleanup, not an AC gap.
- **Duplicate URL / headers write** — tab slots write
  `connection_data.url` / `.headers` on edit; presenter
  `_sync_fields_from_tab` copies again before resolve / Connect. Harmless
  duplication; keep one path when MCP-TM-3 edits the presenter.
- **Dict last-wins on duplicate header names.** `get_data()` and
  `resolve_outbound_fields` use `dict[str, str]`. Two rows with the same
  key collapse. Same as HTTP Headers tables; not a new MCP-only rule.
- **Duck-typed env fan-out** — non-`RequestTab` widgets with a
  `presenter.set_variables` / `set_hidden_keys` receive env updates.
  A tab whose presenter lacks those methods is silently skipped (same
  pattern as duck-typed teardown).
- **Dummy session holder remains** — `_session = object()` from
  PYPOST-1166. Replace with a real outbound session in MCP-TM-3; do not
  invent a second holder here.

Hardcoded labels (**Headers**, **Key**, **Value**) and URL placeholder
`http://127.0.0.1:1080/mcp` match NFR-4 / architecture; they are not
magic-value debt.

## Missing Tests

**Timeout markers: no BLOCKER.** Modules added or edited for this story
already declare explicit `pytest.mark.timeout`:

- `tests/test_mcp_client_tab.py` — `timeout(30)`
- `tests/test_mcp_client_presenter.py` — `timeout(10)`
- `tests/test_tabs_presenter.py` — `timeout(60)`
- PYPOST-1173 method-MCP files keep `timeout(60)`

In-scope AC coverage is present: Headers table widget id and empty-row
UX (`test_mcp_client_tab_has_headers_table`); resolved URL + headers
forwarded to `run(..., headers=)`
(`test_execute_outbound_forwards_resolved_url_and_headers`); empty map
(`test_execute_outbound_forwards_empty_headers`); resolve DEBUG is
count-only (`test_resolve_outbound_fields_logs_header_count_not_values`);
env fan-out on MCP drafts
(`test_on_env_variables_changed_updates_mcp_client_tab`,
`test_on_env_hidden_keys_changed_updates_mcp_client_tab`); Connect INFO
still omits the substring `headers`.

Gaps that remain (none are AC breaks):

- **No hover / hidden-key masking assertion on the MCP Headers table.**
  FR-2.4 reuses `VariableAwareTableWidget` + `VariableHoverResolver`.
  Env keys are pushed (`set_hidden_keys` tests exist). A dedicated hover
  preview / `********` case on this table was left optional in
  architecture.
- **No `execute_outbound` test that reads live table widgets.** Presenter
  tests construct `McpClientConnection(headers=...)` without a tab.
  `_sync_fields_from_tab` is covered only indirectly. A GUI test that
  types a row then calls `execute_outbound` would lock the tab →
  presenter → `run` path.
- **No missing-placeholder case.** Unresolved `{{ missing }}` left as
  text is HTTP parity; add when product wants an MCP-only error.
- **No click-Connect-sends-headers test.** Correctly absent: Connect must
  not call `MCPClientService` in this story. MCP-TM-3 owns the live
  initialize test that `execute_outbound` is used.

Intentionally not missing for 1167: live header-gated MCP server; invoke
UI; Collections persist; inbound proxy headers; Ctrl+H on MCP Client.

## Performance Concerns

None for header resolve + one dict copy into `run`. No new handshake,
worker, or Prometheus series (architecture: counters belong to MCP-TM-3 /
MCP-TM-4).

`tabs_presenter.py` at **779 / 785** is a **capacity** risk for the next
stories that must touch the presenter, not a runtime performance issue.

## Follow-up Tasks

Phase D of the orchestrator creates Jira issues. Step 7 does not, except
citing stories that already exist (1169 / 1170 / 1184).

1. **NON-BLOCKER — intentional epic scope (not incomplete 1167 work)**
   - Live Connect / initialize / `list_tools` **must** call
     `execute_outbound` (or equivalent) so resolved headers cannot be
     dropped. Replace `_session = object()`; use `CONNECTING`; surface
     connect errors. Outbound connect / `list_tools` counters belong here.
   - Verdict: **NON-BLOCKER** (AC: header-aware path exists; live protocol
     is TM-3).
   - Jira: [PYPOST-1169](https://pypost.atlassian.net/browse/PYPOST-1169)

2. **NON-BLOCKER — intentional epic scope**
   - Interactive `call_tool` **must** use the same header-aware
     `execute_outbound` path. Schema forms and result pane are TM-4.
   - Verdict: **NON-BLOCKER**.
   - Jira: [PYPOST-1170](https://pypost.atlassian.net/browse/PYPOST-1170)

3. **NON-BLOCKER — capacity (already ticketed; count is now tighter)**
   - `tabs_presenter.py` is **779 / 785** (~6 LOC). Before MCP-TM-3 /
     MCP-TM-4 / MCP-TM-7 add restore or extra factory lines, extract
     shared insert-before-plus used by HTTP / WS / MCP factories.
     Ticket summary still cites 771/785 from PYPOST-1166; update the
     description when that work starts.
   - Verdict: **NON-BLOCKER**.
   - Jira: [PYPOST-1184](https://pypost.atlassian.net/browse/PYPOST-1184)

4. **NON-BLOCKER — shared Key/Value table (ticket later)**
   - Extract one empty-row `VariableAwareTableWidget` used by HTTP,
     WebSocket handshake, and MCP Client Headers. Do not import
     `request_editor.py` from `mcp_client`.
   - Verdict: **NON-BLOCKER**.
   - Jira: [PYPOST-1186](https://pypost.atlassian.net/browse/PYPOST-1186)

5. **NON-BLOCKER — test gap (ticket later)**
   - Optional: GUI test that edits the Headers table then
     `execute_outbound` asserts `run(..., headers=)` from widget data;
     optional hover / hidden-key `********` on
     `pypost_mcp_client_headers_table`. Keep `pytestmark` timeout; no
     network.
   - Verdict: **NON-BLOCKER**.
   - Jira: [PYPOST-1187](https://pypost.atlassian.net/browse/PYPOST-1187)

6. **NON-BLOCKER — pre-existing/flaky (observed in Step 4)**
   - Node id:
     `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises`
   - Repro: parallel `make test`; suspected Qt `apply_theme` vs uvicorn
     import race. Isolated file run passed. Unrelated to headers table
     assertions.
   - Verdict: **NON-BLOCKER — pre-existing**.
   - Jira: [PYPOST-1188](https://pypost.atlassian.net/browse/PYPOST-1188)

7. **NON-BLOCKER — Step 8 of this task (not a new ticket)**
   - Update `doc/dev/` for MCP Client headers + env resolve:
     `McpClientHeadersTable`, `execute_outbound`, duck-typed env fan-out,
     779/785 presenter budget, secret-safe `header_count` logs.
   - Owned by PYPOST-1167 Step 8.
   - Jira: none
