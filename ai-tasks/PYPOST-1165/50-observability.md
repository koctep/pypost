# PYPOST-1165: Observability Implementation

## Logging Implementation

### Added Logs

No new log lines in this story. Architecture already covers MCP Client
confirm through the PYPOST-1157 picker events: `open_blank_tab` logs
`protocol=%s` from `TabProtocol.value`. After Step 4, confirming **MCP
Client** emits `protocol=mcp_client` on the existing completed event.
Adding a second INFO (or DEBUG) for the stub tab would duplicate that
signal without extra diagnostic value (FR-5.4: no URL, headers, or body
yet; `McpClientTab` is a placeholder until PYPOST-1166).

- **EMERG**: none
- **ALERT**: none
- **CRIT**: none
- **ERR**: none
- **WARNING**: none
- **NOTICE**: none (Python logging has no NOTICE; picker events use INFO)
- **INFO** (existing, reused — not added here):
  - `pypost.ui.presenters.tabs_presenter.handle_new_tab`:
    `new_tab_action_triggered source=%s tabs_before=%d` — picker shown
    for `shortcut` (`Ctrl+N`) or `plus_button` (tab-bar +)
  - `pypost.ui.presenters.tabs_presenter.handle_new_tab`:
    `new_tab_action_cancelled source=%s` — user dismissed the picker;
    no metric (FR-5.5)
  - `pypost.ui.presenters.tabs_presenter.open_blank_tab`:
    `new_tab_action_completed source=%s protocol=%s` — confirm of HTTP,
    WebSocket, or MCP Client. `protocol` is `http`, `websocket`, or
    `mcp_client`
- **DEBUG**: none for the picker / stub. `McpClientTab` and
  `NewTabProtocolPicker` do not log.

`pypost.core.mcp_client_service` ERR/DEBUG logs belong to HTTP method
**MCP** send (`RequestService._execute_mcp`), not this blank-tab path.
Outbound connect / `list_tools` / `call_tool` logging stays with later
editor stories.

### Log Structure

Log format used:

- Structured logs: yes (`snake_case` event then `key=value` pairs)
- Includes context: yes (`source`, `tabs_before`, `protocol`)
- Log levels: INFO
- Payload fields: none (no URL, headers, body, or widget dumps)

## Metrics Implementation (if applicable)

### Performance Metrics

None added. Picker and blank-tab routing are synchronous GUI work; no
latency histogram is required.

### Business Metrics

Reused counter from PYPOST-1157; Step 4 extended the protocol allow-list
only (not a new instrument):

- **gui_new_tab_actions_total{source, protocol}**: completed blank-tab
  choice. Incremented in `TabsPresenter.open_blank_tab` via
  `track_gui_new_tab_action(source, protocol=protocol.value)`.
  - `source`: `plus_button`, `shortcut`, `collections_context`, `unknown`
  - `protocol`: `http`, `websocket`, `mcp_client`, `unknown`
  - Cancel does not increment
  - Collections **New tab** still defaults `protocol=unknown`
  - `_normalize_new_tab_protocol` in `pypost/core/metrics_registry.py`
    (`_NEW_TAB_PROTOCOLS`) is shared by Prometheus (`MetricsRegistry`)
    and OpenTelemetry (`OtelMetricsTracker`)

Prometheus scrape (labels serialized alphabetically):

```text
gui_new_tab_actions_total{protocol="mcp_client",source="plus_button"}
gui_new_tab_actions_total{protocol="mcp_client",source="shortcut"}
```

Do **not** add outbound operation counters (`mcp_client_connect_total`,
`mcp_client_list_tools_total`, `mcp_client_call_tool_total`) here —
architecture R-4 / requirements out-of-scope; those belong with
PYPOST-1166+ editor stories.

Operator inventory: `doc/prometheus_monitoring.md` GUI table now lists
`mcp_client` on `protocol`. `doc/dev/` picker docs stay Step 8.

### System Health Metrics

None added. Opening the MCP Client stub does not change resource gauges.

## Monitoring Integration

Integration with monitoring systems:

- [x] Prometheus metrics (`gui_new_tab_actions_total` protocol allow-list
      includes `mcp_client`; operator table updated)
- [ ] Grafana dashboards (not invented this story)
- [ ] Alerting rules (picker choice is not a failure signal)
- [ ] Log aggregation (ELK, Loki, etc.)

## Validation Results

Validation results:

- [x] Logs are correctly formatted (`event key=value`); MCP Client
      confirm reuses `new_tab_action_completed` with `protocol=mcp_client`
- [x] Metrics are collected correctly:
      `tests/test_metrics_manager.py::test_track_gui_new_tab_action_records_mcp_client_protocol`
      (scrape `protocol="mcp_client"`, not `unknown`);
      `tests/test_metrics_otel.py::test_track_gui_new_tab_action_records_mcp_client_protocol`;
      `tests/test_tabs_presenter.py::test_open_blank_tab_records_mcp_client_protocol`
- [x] Logging works in error / cancel scenarios: cancel still logs
      `new_tab_action_cancelled` and does not increment the counter
      (PYPOST-1157 tests unchanged)
- [x] Large data structures are not logged
- [x] Metrics are available for monitoring (`/metrics` scrape)

## Notes

- STEP 6 is left `[/]` in `00-roadmap.md` — the executing agent does not
  mark `[x]`; that is the acceptance-gate owner's action after review.
- No extra presenter or stub logs: architecture already specified the
  metric allow-list and the existing `protocol=` INFO field.
- HTTP method **MCP** metrics (`mcp_requests_*`) are unchanged (MCP-TM-6).
