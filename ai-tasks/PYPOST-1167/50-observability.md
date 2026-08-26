# PYPOST-1167: Observability Implementation

Header resolution on the MCP Client draft (MCP-TM-5). Logs report **counts
and connection identity only**. Header keys, header values, environment
secrets, and unresolved `{{ placeholders }}` are never written to logs
(NFR-3).

## Logging Implementation

### Added Logs

- **EMERG**: none
- **ALERT**: none
- **CRIT**: none
- **ERR**: none added — outbound failures stay on
  `MCPClientService.run` (`mcp_operation_timeout`, `mcp_operation_failed`)
- **WARNING**: none
- **NOTICE**: none (Python logging has no NOTICE)
- **INFO**: none added. Existing chrome events stay `connection_id` only
  and must not mention headers (Connect is local; MCP-TM-3 owns live
  initialize):
  - `pypost.ui.presenters.mcp_client_presenter.connect_requested`:
    `mcp_client_connect_initiated connection_id=%s`
  - `pypost.ui.presenters.mcp_client_presenter.disconnect_requested`:
    `mcp_client_disconnect_initiated connection_id=%s`
  - `pypost.ui.presenters.mcp_client_presenter.teardown`:
    `mcp_client_presenter_teardown connection_id=%s`
- **DEBUG** (added this story — header resolution, no secret values):
  - `pypost.ui.presenters.mcp_client_presenter.resolve_outbound_fields`:
    `mcp_client_outbound_fields_resolved connection_id=%s header_count=%d`
    — emitted after `TemplateService.render_string` on URL and header
    names/values. `header_count` is `len(resolved_headers)` (`0` when
    the table is empty). Does **not** log URL text, header keys, header
    values, or env maps.
- **DEBUG** (reused — PYPOST-1173, still the wire-side check):
  - `pypost.core.mcp_client_service.MCPClientService.run`:
    `mcp_operation_start url=%s operation=%s header_count=%d`
    — length of the map passed into `create_mcp_http_client`. Header
    **keys** and **values** are not logged. Method **MCP** Send
    (`RequestService._execute_mcp`) has no second count log; it reuses
    this start event.

`McpClientTab`, `McpClientHeadersTable`, and hover preview do not log.

### Log Structure

Log format used:

- Structured logs: yes (`snake_case` event then `key=value` pairs)
- Includes context: yes (`connection_id`, `header_count`; service start
  still has `url`, `operation`, `header_count`)
- Log levels: INFO (chrome lifecycle), DEBUG (resolve + operation start)
- Payload fields: none for secrets (no header map, no Bearer tokens,
  no env snapshot)

## Metrics Implementation (if applicable)

No new metrics. Architecture does not add outbound MCP counters here
(`list_tools` / `call_tool` totals belong to MCP-TM-3 / MCP-TM-4).
Header forwarding is a wiring property, not a Prometheus dimension.

### Performance Metrics

Added performance metrics:

- **Response time**: none new — existing `mcp_operation_success elapsed`
  DEBUG log and `ResponseData.elapsed_time` on `MCPClientService.run`
- **Throughput**: none new
- **Error rate**: none new — existing `mcp_operation_timeout` /
  `mcp_operation_failed`

Method **MCP** still uses existing request metrics from PYPOST-1173:

- `RequestService._execute_mcp` — `track_request_sent(request.method)`
- `RequestService._execute_mcp` — `track_response_received(method, status)`

### Business Metrics

Business metrics:

- none added — environment-resolved auth is not a conversion event

### System Health Metrics

System health metrics:

- **Resource usage**: CPU, memory, disk — unchanged; not in scope
- **Component status**: outbound MCP failures remain on service ERROR logs

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics — no new series
- [ ] Grafana dashboards — no new dashboard
- [ ] Alerting rules — header drop is a wiring defect, not a runtime
      alert
- [x] Log aggregation (ELK, Loki, etc.) — loggers
      `pypost.ui.presenters.mcp_client_presenter` (resolve DEBUG) and
      `pypost.core.mcp_client_service` (`header_count` on start)

Catalog updates for `doc/dev/logging.md` belong to Step 8, not this step.

## Validation Results

Validation results:

- [x] Logs are correctly formatted (`event key=value`)
- [x] Metrics are collected correctly (unchanged; no new counters)
- [x] Logging works in error scenarios (existing service ERROR logs;
      no header dump)
- [x] Large data structures are not logged (count only)
- [x] Metrics are available for monitoring (pre-existing request metrics
      on method **MCP**)
- [x] Secret values never appear in resolve logs
      (`test_mcp_client_presenter.py::test_resolve_outbound_fields_logs_header_count_not_values`)
- [x] Connect INFO still omits URL and the substring `headers`
      (`tests/test_mcp_client_tab.py::test_presenter_logs_connect_disconnect_teardown`)
- [x] Service still logs count, not values
      (`tests/test_mcp_client_service.py::test_run_logs_header_count_not_values`)

## Notes

- Resolve DEBUG is the MCP Client story's header-resolution event.
  Service `header_count` confirms the same map reached Streamable HTTP.
  Duplicating keys (proxy `header_keys=%s`) was rejected: names like
  `Authorization` plus a count already identify auth; values must stay
  out.
- Connect does **not** call `resolve_outbound_fields` in this story.
  MCP-TM-3 must call `execute_outbound` so live initialize cannot skip
  both the resolve DEBUG and the service start `header_count`.
- STEP 6 is left `[/]` in `00-roadmap.md` — the executing agent does not
  mark `[x]`.
