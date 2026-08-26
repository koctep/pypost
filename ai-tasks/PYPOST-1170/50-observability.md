# PYPOST-1170: Observability Implementation

Interactive `call_tool` on the MCP Client tab (MCP-TM-4). Logs identify
**connection_id**, **kind** (`invoke`), and optional **reason** tokens only.
Secrets, URL text, header names/values, tool names, and argument payloads
are never written to logs.

`tabs_presenter.py` is unchanged (779 / 785). Counters live on the metrics
stack; `McpClientPresenter` already accepts optional `metrics=` so tests
can record `mcp_client_call_tool_total` without growing the tab factory.

## Logging Implementation

### Added Logs

- **EMERG**: none
- **ALERT**: none
- **CRIT**: none
- **ERR**:
  - `pypost.ui.presenters.mcp_client_presenter._on_invoke_error`:
    `mcp_client_call_tool_failed connection_id=%s kind=%s` — worker
    `ExecutionError` or unexpected failure. Does **not** log the error
    message, `detail`, URL, headers, tool name, or arguments.
  - `pypost.ui.presenters.mcp_client_presenter._on_invoke_ok`:
    `mcp_client_call_tool_failed connection_id=%s kind=%s
    reason=invalid_result` — JSON body missing or not a result object.
    No body dump.
- **WARNING**: none new for Invoke (empty URL remains a Connect/Refresh
  WARNING from MCP-TM-3)
- **NOTICE**: none (Python logging has no NOTICE)
- **INFO**:
  - `mcp_client_call_tool_initiated connection_id=%s kind=%s` — logged
    only after validation succeeds and a worker `call_tool` is started
  - `mcp_client_call_tool_succeeded connection_id=%s kind=%s` — worker
    returned `ResponseData`, including tool `isError: true` (failed
    **call**, not failed Connect)
- **DEBUG**:
  - `mcp_client_call_tool_ignored connection_id=%s kind=%s reason=%s` —
    `in_flight`, `not_connected`, `no_selection`, `validation`, or
    `stale` (generation mismatch). Reason token only; no field values.
  - Existing (unchanged): `mcp_client_outbound_fields_resolved`
    (`header_count` only), `mcp_client_outbound_worker_started`

`MCPClientService` still logs `mcp_operation_start` with `url=` at DEBUG
(PYPOST-1173, HTTP method **MCP**). This story does not add URL to
presenter or worker logs. `tabs_presenter.py` has no new log lines.

### Log Structure

Log format used:

- Structured logs: yes (`snake_case` event then `key=value` pairs)
- Includes context: yes (`connection_id`, `kind`, `reason`)
- Log levels: INFO (initiate + settle success), ERROR (worker / invalid
  result), DEBUG (ignored invoke)
- Payload fields: none for secrets (no header map, no Bearer tokens, no
  env snapshot, no URL, no argument object, no tool name)

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:

- **Response time**: none new — existing `mcp_operation_success elapsed`
  DEBUG on `MCPClientService.run` remains the wire-side timer; the result
  pane shows `elapsed_time` to the user
- **Throughput**: `mcp_client_call_tool_total` (Invoke volume)
- **Error rate**: `mcp_client_call_tool_total{result="error"}`

### Business Metrics

Business metrics:

- **mcp_client_call_tool_total{result}**: worker invoke settle only
  (`success` / `error`). Distinct from
  `mcp_client_connect_total`, `mcp_client_list_tools_total`, and inbound
  `mcp_requests_received_total`.
  - `success`: `ResponseData` parsed, including `isError: true`
  - `error`: `ExecutionError` or unparseable result body
  - Client-side validation (required empty, bad JSON, no selection,
    disconnected) does **not** increment
  Location: `McpClientPresenter._record_call_tool_outcome` via
  `MetricsRegistry.track_mcp_client_call_tool` (also OTel tracker and
  `MetricsTrackingMixin`)

Prometheus scrape examples:

```text
mcp_client_call_tool_total{result="success"}
mcp_client_call_tool_total{result="error"}
```

### System Health Metrics

System health metrics:

- **Resource usage**: CPU, memory, disk — unchanged
- **Component status**: failed Invoke stays CONNECTED; session enum is not
  a Prometheus gauge this story

## Monitoring Integration

Integration with monitoring systems:

- [x] Prometheus metrics (`mcp_client_call_tool_total` on
      `MetricsRegistry`, OTel tracker, and `MetricsTrackingMixin`)
- [ ] Grafana dashboards — no new dashboard
- [ ] Alerting rules — not invented this story
- [x] Log aggregation (ELK, Loki, etc.) — logger
      `pypost.ui.presenters.mcp_client_presenter` (and worker unexpected
      ERROR on `pypost.ui.presenters.mcp_client_worker`)

`McpClientPresenter` takes optional `metrics=`. `add_blank_mcp_client_tab`
does not pass `TabsPresenter._metrics` because this story must not grow
`tabs_presenter.py`. Unit/GUI tests inject `MetricsRegistry`. Factory
injection remains a follow-up so `/metrics` scrape records live Invoke in
the running app.

Catalog updates for `doc/dev/logging.md` and `doc/prometheus_monitoring.md`
belong to Step 8.

## Validation Results

Validation results:

- [x] Logs are correctly formatted (`event key=value`)
- [x] Metrics are collected correctly
      (`tests/test_metrics_registry.py::TestMetricsRegistryMcpCounters.test_track_mcp_client_call_tool`,
      `tests/test_metrics_otel.py::test_track_mcp_client_call_tool_increments_counter`,
      `tests/test_mcp_client_tab.py::test_invoke_call_tool_displays_structured_result`)
- [x] Logging works in error scenarios
      (`test_invoke_error_keeps_connected_and_tools` asserts
      `mcp_client_call_tool_failed` and omits the secret token / URL /
      `headers` / argument text)
- [x] Large data structures are not logged (connection_id and kind only)
- [x] Metrics are available for monitoring (registry + OTel instruments;
      live GUI scrape waits on factory injection)
- [x] Invoke INFO omits URL, `headers`, arguments, and tool names
      (`test_invoke_call_tool_displays_structured_result`)
- [x] Client validation does not increment `mcp_client_call_tool_total`
      (`test_empty_required_form_field_does_not_call_tool`)
- [x] `tabs_presenter.py` not edited (785 LOC cap, no growth)

## Notes

- STEP 6 is left `[/]` in `00-roadmap.md` — the executing agent does not
  mark `[x]`.
- Inbound `mcp_requests_received_total{method="tools/call"}` remains the
  **server** tools PyPost exposes. Outbound Invoke uses
  `mcp_client_call_tool_total` so the two must not be summed together.
- Validation and in-flight second clicks log DEBUG ignore and do not
  increment counters.
- Stale worker results (bumped generation) log DEBUG ignore and do not
  increment counters.
- Tool `isError: true` is INFO success for the **transport** counter and
  an error presentation in the result pane.
