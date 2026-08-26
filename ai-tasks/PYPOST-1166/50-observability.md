# PYPOST-1166: Observability Implementation

Draft MCP Client tab shell (MCP-TM-2). Connect is local chrome only; live
initialize and outbound operation counters stay with MCP-TM-3 / MCP-TM-4.

## Logging Implementation

### Added Logs

- **EMERG**: none
- **ALERT**: none
- **CRIT**: none
- **ERR**: none
- **WARNING**: none
- **NOTICE**: none (Python logging has no NOTICE; lifecycle uses INFO)
- **INFO** (added this story — local chrome, not live MCP):
  - `pypost.ui.presenters.mcp_client_presenter.connect_requested`:
    `mcp_client_connect_initiated connection_id=%s` — user clicked
    **Connect**; session holder is local only (no `MCPClientService`)
  - `pypost.ui.presenters.mcp_client_presenter.disconnect_requested`:
    `mcp_client_disconnect_initiated connection_id=%s` — user clicked
    **Disconnect**
  - `pypost.ui.presenters.mcp_client_presenter.teardown` (Step 4, kept):
    `mcp_client_presenter_teardown connection_id=%s` — tab close /
    `TabsPresenter.close_tab` duck-typed teardown (FR-4.2 / NFR-4)
- **INFO** (existing, reused — not added here):
  - `pypost.ui.presenters.tabs_presenter.handle_new_tab`:
    `new_tab_action_triggered source=%s tabs_before=%d`
  - `pypost.ui.presenters.tabs_presenter.handle_new_tab`:
    `new_tab_action_cancelled source=%s`
  - `pypost.ui.presenters.tabs_presenter.open_blank_tab`:
    `new_tab_action_completed source=%s protocol=%s` — confirm of MCP
    Client still emits `protocol=mcp_client` (PYPOST-1165)
- **DEBUG**: none for the draft shell. `McpClientTab`, connection bar, and
  tool browser do not log.

URL text, headers, env vars, and widget dumps are not logged. Live
`list_tools` / `call_tool` logging belongs to MCP-TM-3 / MCP-TM-4.

`pypost.core.mcp_client_service` ERR/DEBUG logs belong to HTTP method
**MCP** send (`RequestService._execute_mcp`), not this draft-tab path.

### Log Structure

Log format used:

- Structured logs: yes (`snake_case` event then `key=value` pairs)
- Includes context: yes (`connection_id`; picker path still has `source`,
  `tabs_before`, `protocol`)
- Log levels: INFO
- Payload fields: none (no URL, headers, body, or session object dumps)

## Metrics Implementation (if applicable)

### Performance Metrics

None added. Local Connect / Disconnect / teardown are synchronous GUI
work; no latency histogram is required.

### Business Metrics

None added this story. Architecture and requirements forbid outbound
operation counters here (`mcp_client_connect_total`,
`mcp_client_list_tools_total`, `mcp_client_call_tool_total` — MCP-TM-3 /
MCP-TM-4).

Reused from PYPOST-1165 / PYPOST-1157 (unchanged):

- **gui_new_tab_actions_total{source, protocol}**: completed blank-tab
  choice. Incremented in `TabsPresenter.open_blank_tab` via
  `track_gui_new_tab_action(source, protocol=protocol.value)`.
  - `protocol`: includes `mcp_client` (allow-list in
    `pypost/core/metrics_registry.py`)
  - Cancel does not increment

Prometheus scrape (labels serialized alphabetically):

```text
gui_new_tab_actions_total{protocol="mcp_client",source="plus_button"}
gui_new_tab_actions_total{protocol="mcp_client",source="shortcut"}
```

Picker / metrics wiring was not changed.

### System Health Metrics

None added. Local chrome state does not change resource gauges or live
MCP session counts.

## Monitoring Integration

Integration with monitoring systems:

- [x] Prometheus metrics (`gui_new_tab_actions_total` already includes
      `protocol=mcp_client`; no new instruments)
- [ ] Grafana dashboards (not invented this story)
- [ ] Alerting rules (local Connect is not a failure signal)
- [ ] Log aggregation (ELK, Loki, etc.)

## Validation Results

Validation results:

- [x] Logs are correctly formatted (`event key=value`); connect /
      disconnect / teardown include `connection_id` only
- [x] Metrics are collected correctly: no new counters; existing
      `protocol=mcp_client` tests remain the source of truth
      (`tests/test_metrics_manager.py::test_track_gui_new_tab_action_records_mcp_client_protocol`,
      `tests/test_metrics_otel.py::test_track_gui_new_tab_action_records_mcp_client_protocol`,
      `tests/test_tabs_presenter.py::test_open_blank_tab_records_mcp_client_protocol`)
- [x] Logging works in chrome scenarios:
      `tests/test_mcp_client_tab.py::test_presenter_logs_connect_disconnect_teardown`
- [x] Large data structures are not logged
- [x] Metrics are available for monitoring (`/metrics` scrape of the
      existing GUI counter; no live MCP counters)

## Notes

- STEP 6 is left `[/]` in `00-roadmap.md` — the executing agent does not
  mark `[x]`; that is the acceptance-gate owner's action after review.
- Teardown INFO exists so operators can confirm close releases the
  outbound holder even while Connect is still a no-network stub
  (Postman disconnect-leak lesson in architecture R-1).
- HTTP method **MCP** metrics (`mcp_requests_*`) and inbound MCP server
  logs are unchanged.
