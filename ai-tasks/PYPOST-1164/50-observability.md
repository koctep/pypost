# PYPOST-1164: Observability Implementation

## Scope Note

PYPOST-1164 is a research and decomposition story. No `pypost/` production code, daemon process,
or service was added or changed — Steps 3 and 4 were **N/A** (no behavior to test, no code to
write). There is therefore nothing that executes in production **for this task**, so PYPOST-1164
itself has no logs and no metrics to add.

The epic it decomposes ([PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155)) and the
MCP Client child stories carry observability obligations identified during research. Those are
confirmed below as cross-references to the child implementation stories — not new decisions
invented for this step.

## Logging Implementation

### Added Logs

None added by PYPOST-1164 — no code exists for this task to log from.

Existing inbound MCP server logging (`doc/dev/logging.md`, `doc/dev/mcp_integration.md`,
`doc/dev/mcp_proxy.md`) and WebSocket lifecycle logging from Epic PYPOST-1123 are unchanged by
this research task. Blank-tab creation paths do not introduce new log events in the research
scope; any future logging for MCP Client connect/disconnect, `list_tools`, or `call_tool` would
be owned by the implementation stories that add the behavior (MCP-TM-2 … MCP-TM-4).

### Log Structure

Not applicable to PYPOST-1164's own changes (no code, no log calls).

## Metrics Implementation (if applicable)

Not applicable to PYPOST-1164 itself — no code, no metrics registry entries added by this task.

### Research finding — new-tab protocol attribution (NFR-5 / FR-1.1)

[`20-architecture.md`](20-architecture.md) section **R-3 Metrics extension** documents that
`track_gui_new_tab_action(source)` today records only the creation source (`plus_button`,
`shortcut`, `collections_context`, `unknown`). WS-TM-1 (PYPOST-1157) adds a `protocol` label
(`http` | `websocket`). Functional requirements FR-1.1 and NFR-5 require MCP Client to extend
that dimension when the third protocol ships.

**Deferred to MCP-TM-1:**

- Extend `track_gui_new_tab_action` (or the WS-TM-1 sibling counter) with `protocol=mcp_client`
  when the user chooses **MCP Client** from `NewTabProtocolPicker`.
- Wire the label from `TabsPresenter.open_blank_tab(protocol, source)` after the protocol picker
  resolves.
- Add tests in `tests/test_tabs_presenter.py` (proposed red test in MCP-TM-1 Step 3).

### Research finding — outbound MCP client operation counters (NFR-5)

[`20-architecture.md`](20-architecture.md) and NFR-5 require outbound Connect, `list_tools`, and
`call_tool` actions to be attributable separately from inbound `mcp_requests_received_total`.

**Deferred to MCP-TM-3 and MCP-TM-4:**

- New counters (e.g. `mcp_client_connect_total`, `mcp_client_list_tools_total`,
  `mcp_client_call_tool_total`) — distinct from inbound server metrics.
- Wire from `McpClientPresenter` / worker after Connect and Invoke succeed or fail.
- Proposed test locations in `20-architecture.md` red-test table for MCP-TM-3.

### Performance Metrics

None added by this task. MCP Client tabs may hold tab-scoped `ClientSession` objects after
Connect (MCP-TM-3); session governance and timeout exposure (today 25s in `MCPClientService`) are
implementation concerns, not research deliverables.

### Business Metrics

Designed, not yet built — owned by child stories:

- **New tab by source and protocol**: `protocol=mcp_client` dimension on GUI new-tab counter
  (MCP-TM-1).
- **Outbound client operations**: connect / list_tools / call_tool counters (MCP-TM-3, MCP-TM-4).

### System Health Metrics

None added by this task. Inbound MCP proxy and local server health metrics remain unchanged.

## Monitoring Integration

- [ ] Prometheus metrics for `protocol=mcp_client` on new-tab counter — deferred to MCP-TM-1
- [ ] Outbound MCP client operation counters — deferred to MCP-TM-3 / MCP-TM-4
- [ ] Existing inbound `mcp_requests_received_total` and WebSocket metrics unchanged

## Validation Results

- [x] Confirmed no production code changed in PYPOST-1164
- [x] Metrics extension requirements documented in `20-architecture.md` R-3 and child story
  acceptance criteria (MCP-TM-1, MCP-TM-3, MCP-TM-4)
- [x] Owning stories identified with proposed test locations (no Jira links — Phase D)
- [x] No logging or metrics obligation silently dropped — deferred items named explicitly

## Notes

- STEP 6 is left at `[/]` in `00-roadmap.md` — per `td-roadmap`, the executing agent does not
  mark its own step `[x]`; that is the acceptance-gate owner's action after review passes.
- Full observability implementation for MCP Client tab flows will be validated when child
  stories MCP-TM-1 … MCP-TM-8 run their own Step 6 cycles.
