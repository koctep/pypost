# PYPOST-1170: Technical Debt Analysis

PYPOST-1170 (MCP-TM-4) added select → fill → invoke → inspect on the MCP
Client tab: Qt-free `mcp_client_arg_schema`, catalog `inputSchema`,
schema form / JSON fallback / no-arg invoke, result pane with elapsed
time, GUI-thread `resolve_outbound_fields` then reused
`McpClientOutboundWorker` `operation=call_tool` `kind=invoke`, failed
invoke staying CONNECTED with tools kept, `sanitize_text` on result
content, and outbound `mcp_client_call_tool_total`.

There is **no AC-breaking debt** in this story's change. Remaining items
are intentional later MCP-TM work, presenter LOC headroom (factory still
does not inject `metrics=`), a copied headers table, and a few untested
edges. None of those items block Step 8.

Jira keys below that already exist are cited for context. **New follow-up
issues are not created in this step** (Phase D / orchestrator). Already
linked keys used here:
[PYPOST-1184](https://pypost.atlassian.net/browse/PYPOST-1184),
[PYPOST-1186](https://pypost.atlassian.net/browse/PYPOST-1186),
[PYPOST-1168](https://pypost.atlassian.net/browse/PYPOST-1168).

## Shortcuts Taken

1. **No held SDK `ClientSession`.** Architecture Option A: chrome
   `CONNECTED` is last successful discovery. Each Invoke is one-shot
   initialize + `call_tool` + close with the same resolved URL/headers
   as Connect. Parent PYPOST-1164 preferred a tab-lifetime session;
   this story did not add a holder. Stateful Streamable HTTP session IDs
   remain a later optional follow-up, not an AC gap.
2. **Factory does not inject `metrics=`.** `McpClientPresenter` accepts
   optional `metrics=` and tests pass a `MetricsRegistry`.
   `add_blank_mcp_client_tab` still constructs the presenter with only
   `env_vars` / `hidden_keys`. This story made **zero** edits to
   `tabs_presenter.py` (779 / 785). Live `/metrics` scrape for Invoke in
   the running app waits on factory injection **after** PYPOST-1184
   extract.
3. **Invoke does not call `execute_outbound`.** Live path is GUI resolve
   then worker `run`. Sync `execute_outbound` remains for unit tests.
   The header contract is the same; the method body is not reused on
   `QThread` (NFR-5 / architecture Option C rejected).
4. **Dummy session holder remains.** Success still sets
   `_session = object()` so teardown / Disconnect have something to
   drop. `MCPClientService.run` still opens and closes Streamable HTTP
   per call. Replacing the dummy with a real holder is not this story.
5. **Simple form is flat primitives only.** Nested objects, arrays,
   `$ref` / `oneOf` / `anyOf` / `allOf`, and unknown types use the JSON
   object editor. Matches Inspector-style fallback and FR-2.3. Not a
   full JSON Schema form renderer.
6. **Image / audio content is a typed placeholder.** Result pane shows
   `[image content]` / `[audio content]` plus JSON for other block
   types. No preview widgets. Matches architecture R-1 deferral.
7. **No `outputSchema` validation** of `structuredContent`. The pane
   dumps sanitized JSON. Spec-level output checking is out of scope.
8. **First `tools/list` page only.** `nextCursor` is still ignored
   (unchanged from PYPOST-1169 / `MCPClientService`).
9. **Disconnect does not `requestInterruption` on the worker.**
   Generation is bumped so late results are ignored; `_drop_worker`
   disconnects signals and `deleteLater`. A still-running `anyio.run`
   may finish until the 25s service timeout. Same as Connect / Refresh.
10. **User-facing docs not rewritten here.** MCP-TM-8
    ([PYPOST-1168](https://pypost.atlassian.net/browse/PYPOST-1168)).
    `doc/dev/` for invoke belongs to Step 8 of this task.
11. **HTTP method MCP and Collections persist left alone.** MCP-TM-6 /
    MCP-TM-7. Convert-on-open and last-tool save are not incomplete
    1170 work.

## Code Quality Issues

Implementation matches architecture: invoke UI lives in
`McpClientPresenter` and `mcp_client` widgets (`tool_invoke_form`,
`mcp_result_view`); classifier is Qt-free in
`pypost.core.mcp_client_arg_schema`; `tabs_presenter.py` stays a thin
factory at **779 / 785**.

- **Presenter LOC is still tight — `tabs_presenter.py` 779 / 785.** This
  story spent **zero** of the remaining six lines. Factory metrics
  injection is deferred for that reason (see Shortcuts). MCP-TM-6 /
  MCP-TM-7 must extract shared insert-before-plus **before** adding
  restore or extra factory kwargs. Already ticketed as PYPOST-1184
  (ticket text may still cite 771/785 from PYPOST-1166).
- **Dummy session holder remains.** `_session = object()` after
  successful discovery. A real outbound session is optional later work
  if one-shot `call_tool` is not enough for session-id servers.
- **`execute_outbound` is still GUI-thread / blocking.** Fine for unit
  tests. Interactive Invoke uses the worker so the window is not frozen.
- **Triplicated Key/Value tables** — unchanged from PYPOST-1167.
  `McpClientHeadersTable` is still a copy. Already ticketed as
  PYPOST-1186. This story did not change the headers table.
- **Duplicate URL / headers write** — tab slots write
  `connection_data`; presenter `_sync_fields_from_tab` copies again
  before resolve. Harmless; keep one path if a later story edits the
  presenter.
- **Dict last-wins on duplicate header names.** Same as HTTP Headers
  tables.
- **Duck-typed env fan-out** — unchanged; tabs without
  `set_variables` / `set_hidden_keys` are skipped.

Hardcoded copy (**Invoke**, **Use JSON**, **Invoking...**, **Elapsed**,
**Result**, **This tool takes no arguments.**) matches architecture;
they are not magic-value debt.

## Missing Tests

**Timeout markers: no BLOCKER.** Modules added or edited for this story
already declare explicit `pytest.mark.timeout`:

- `tests/test_mcp_client_tab.py` — `timeout(30)`
- `tests/test_mcp_client_arg_schema.py` — `timeout(10)`
- `tests/test_mcp_client_presenter.py` — `timeout(10)`
- `tests/test_tabs_presenter.py` — `timeout(60)`
- `tests/test_metrics_registry.py` — `timeout(30)`
- `tests/test_metrics_otel.py` — `timeout(30)`

In-scope AC coverage is present: Invoke shows structured result and
elapsed; `ExecutionError` stays CONNECTED with tools kept; nested schema
JSON fallback sends an object; empty required form field does not call
`run`; result sanitizer masks hidden values; `mcp_client_call_tool_total`
increments on worker settle only; secret-safe logs (no URL, headers,
arguments, or tool names). Classifier covers simple_form / json_only /
no_args.

Gaps that remain (none are AC breaks):

- **No live Streamable HTTP integration test.** GUI tests mock
  `MCPClientService.run`. Optional later; not required for MCP-TM-4 AC.
- **No GUI test that types Headers-table rows then Invoke.** Connect /
  Invoke tests seed `McpClientConnection.headers` or mock `run`. Widget
  → `_sync_fields_from_tab` → `call_tool` is still an uncovered typing
  path (same class of gap as PYPOST-1169 Connect).
- **No dedicated no-arg Invoke GUI test.** Classifier covers
  empty-properties → `no_args`; the GUI path is exercised indirectly.
- **No image / audio result-block widget test.** Placeholders are
  implemented; no dedicated assertion.
- **No factory scrape test that blank MCP tabs increment
  `mcp_client_call_tool_total` on `/metrics`.** Counters work when
  `metrics=` is injected; the running factory does not inject yet.
- **No pagination / `nextCursor` test.** Out of scope (first page
  only).

Intentionally not missing for 1170: Collections persist; HTTP method
**MCP** migration; inbound **MCP Servers…**; Ctrl+H on MCP Client;
held `ClientSession`.

## Performance Concerns

Each Invoke is one-shot initialize + `call_tool` + close (up to
`MCP_TOTAL_TIMEOUT` 25s on the worker). That is acceptable for
interactive inspect. Holding a session to avoid re-initialize is
optional later work, not a runtime bug in this story.

`tabs_presenter.py` at **779 / 785** is a **capacity** risk for factory
metrics injection and later stories, not a runtime performance issue.

No Grafana dashboards or alerting rules were added (Step 6).

## Follow-up Tasks

Phase D of the orchestrator creates Jira issues. Step 7 does not.
Existing keys are cited; nothing new is filed here.

1. **NON-BLOCKER — capacity (already ticketed; still 779 / 785)**
   - Extract shared insert-before-plus used by HTTP / WS / MCP
     factories. **Then** pass `metrics=self._metrics` into
     `McpClientPresenter` so live Connect / Refresh / Invoke hit
     Prometheus. Factory injection is deferred **because** this file is
     779 / 785 and this story must not grow it.
   - Verdict: **NON-BLOCKER**.
   - Jira: [PYPOST-1184](https://pypost.atlassian.net/browse/PYPOST-1184)

2. **NON-BLOCKER — shared Key/Value table (still relevant)**
   - Extract one empty-row `VariableAwareTableWidget` used by HTTP,
     WebSocket handshake, and MCP Client Headers. This story did not
     change the headers table.
   - Verdict: **NON-BLOCKER**.
   - Jira: [PYPOST-1186](https://pypost.atlassian.net/browse/PYPOST-1186)

3. **NON-BLOCKER — intentional epic scope (user docs)**
   - Rewrite user docs for MCP Client tab mode, including the invoke
     loop (select, schema form / JSON, result pane), and disambiguate
     inbound vs outbound MCP. Not this story's Step 8 (`doc/dev/` only).
   - Verdict: **NON-BLOCKER**.
   - Jira: [PYPOST-1168](https://pypost.atlassian.net/browse/PYPOST-1168)

4. **NON-BLOCKER — Step 8 of this task (not a new ticket)**
   - Update `doc/dev/` for interactive Invoke: worker `kind=invoke` vs
     `execute_outbound`, form vs JSON vs no-arg, failed-invoke chrome,
     `mcp_client_call_tool_total` vs inbound
     `mcp_requests_received_total`, factory metrics injection deferred
     at 779 / 785.
   - Owned by PYPOST-1170 Step 8.
   - Jira: none
