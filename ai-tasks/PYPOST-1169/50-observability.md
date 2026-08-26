# PYPOST-1169: Observability Implementation

Live Connect / Refresh `list_tools` on the MCP Client tab (MCP-TM-3). Logs
and counters identify **connection_id**, **kind** (`connect` / `refresh`),
and **tool_count** only. Secrets, header names/values, and URL text (including
templated or token-bearing URLs) are never written to logs.

`tabs_presenter.py` is unchanged. Counters live on the metrics stack;
`McpClientPresenter` accepts optional `metrics=` so tests and a later factory
injection can record them without growing the 785-LOC tab factory.

## Logging Implementation

### Added Logs

- **EMERG**: none
- **ALERT**: none
- **CRIT**: none
- **ERR**:
  - `pypost.ui.presenters.mcp_client_presenter._on_list_error`:
    `mcp_client_list_tools_failed connection_id=%s kind=%s` — worker
    `ExecutionError` or unexpected failure. Does **not** log the error
    message, `detail`, URL, or headers (hidden env values must not leak).
  - `pypost.ui.presenters.mcp_client_presenter._on_list_ok`:
    `mcp_client_list_tools_failed connection_id=%s kind=%s reason=invalid_tools`
    — JSON body missing `tools` or not parseable. No body dump.
  - `pypost.ui.presenters.mcp_client_worker.McpClientOutboundWorker.run`
    (Step 4, kept):
    `mcp_client_outbound_worker_unexpected generation=%s kind=%s` — uncaught
    exception on the worker. No URL.
- **WARNING**:
  - `pypost.ui.presenters.mcp_client_presenter._start_list`:
    `mcp_client_list_rejected connection_id=%s kind=%s reason=empty_url` —
    resolved URL is empty; `run` is not called. Reason token only, not the
    URL string.
- **NOTICE**: none (Python logging has no NOTICE)
- **INFO** (chrome + discovery outcome):
  - Existing: `mcp_client_connect_initiated connection_id=%s`
  - Added: `mcp_client_refresh_initiated connection_id=%s`
  - Added: `mcp_client_list_tools_succeeded connection_id=%s kind=%s tool_count=%d`
    — `tool_count` is the parsed row count after skipping empty names.
    Tool **names** and **descriptions** are not logged.
  - Existing (unchanged): `mcp_client_disconnect_initiated`,
    `mcp_client_presenter_teardown`
- **DEBUG** (reused / small additions, still no URL or headers):
  - Existing: `mcp_client_outbound_fields_resolved connection_id=%s header_count=%d`
  - Existing: `mcp_client_outbound_worker_started generation=%s kind=%s`
  - Added: `mcp_client_list_tools_ignored connection_id=%s kind=%s` — stale
    generation after Disconnect / teardown / superseded list.

`MCPClientService` still logs `mcp_operation_start` with `url=` at DEBUG
(PYPOST-1173, HTTP method **MCP**). This story does not add URL to presenter
or worker logs. `tabs_presenter.py` has no new log lines.

### Log Structure

Log format used:

- Structured logs: yes (`snake_case` event then `key=value` pairs)
- Includes context: yes (`connection_id`, `kind`, `tool_count`, `reason`,
  `generation`)
- Log levels: INFO (lifecycle + success count), WARNING (empty URL),
  ERROR (list failure), DEBUG (resolve, worker start, stale result)
- Payload fields: none for secrets (no header map, no Bearer tokens, no
  env snapshot, no URL)

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:

- **Response time**: none new — existing `mcp_operation_success elapsed`
  DEBUG on `MCPClientService.run` remains the wire-side timer
- **Throughput**: `mcp_client_list_tools_total` (Connect + Refresh volume)
- **Error rate**: `mcp_client_connect_total{result="error"}` and
  `mcp_client_list_tools_total{result="error",operation=...}`

### Business Metrics

Business metrics:

- **mcp_client_connect_total{result}**: Connect settle only
  (`success` / `error`). Refresh does **not** increment this counter.
  Location: `McpClientPresenter._record_list_outcome` via
  `MetricsRegistry.track_mcp_client_connect`
- **mcp_client_list_tools_total{result,operation}**: every Connect or
  Refresh settle, including empty-URL reject and invalid tools parse.
  `operation` is `connect` or `refresh`. Distinct from inbound
  `mcp_requests_received_total`.
  Location: `McpClientPresenter._record_list_outcome` via
  `track_mcp_client_list_tools`

Prometheus scrape examples:

```text
mcp_client_connect_total{result="success"}
mcp_client_connect_total{result="error"}
mcp_client_list_tools_total{operation="connect",result="success"}
mcp_client_list_tools_total{operation="refresh",result="error"}
```

`call_tool` counters remain MCP-TM-4.

### System Health Metrics

System health metrics:

- **Resource usage**: CPU, memory, disk — unchanged
- **Component status**: Connect vs Refresh error policy is visible in
  chrome plus the `operation` label; session enum is not a Prometheus
  gauge this story

## Monitoring Integration

Integration with monitoring systems:

- [x] Prometheus metrics (`mcp_client_connect_total`,
      `mcp_client_list_tools_total` on `MetricsRegistry`, OTel tracker,
      and `MetricsTrackingMixin`)
- [ ] Grafana dashboards — no new dashboard
- [ ] Alerting rules — not invented this story
- [x] Log aggregation (ELK, Loki, etc.) — logger
      `pypost.ui.presenters.mcp_client_presenter` (and worker unexpected
      ERROR on `pypost.ui.presenters.mcp_client_worker`)

`McpClientPresenter` takes optional `metrics=`. `add_blank_mcp_client_tab`
does not pass `TabsPresenter._metrics` because this story must not grow
`tabs_presenter.py`. Unit/GUI tests inject `MetricsRegistry`. Factory
injection is a follow-up (Step 7) so `/metrics` scrape records live
Connect/Refresh in the running app.

Catalog updates for `doc/dev/logging.md` and `doc/prometheus_monitoring.md`
belong to Step 8.

## Validation Results

Validation results:

- [x] Logs are correctly formatted (`event key=value`)
- [x] Metrics are collected correctly
      (`tests/test_metrics_registry.py::TestMetricsRegistryMcpCounters.test_track_mcp_client_connect`,
      `test_track_mcp_client_list_tools`;
      `tests/test_metrics_otel.py::test_track_mcp_client_connect_and_list_tools_increments_counters`;
      `tests/test_mcp_client_tab.py::test_connect_and_refresh_record_outbound_metrics`)
- [x] Logging works in error scenarios
      (`test_connect_error_leaves_disconnected_and_empty_tools` asserts
      `mcp_client_list_tools_failed` and omits the secret token / URL /
      `headers`)
- [x] Large data structures are not logged (count and kind only)
- [x] Metrics are available for monitoring (registry + OTel instruments;
      live GUI scrape waits on factory injection)
- [x] Connect INFO still omits URL and the substring `headers`
      (`test_presenter_logs_connect_disconnect_teardown`,
      `test_connect_success_logs_tool_count_not_url_or_headers`,
      `test_refresh_initiated_log_omits_url_and_headers`)
- [x] `tabs_presenter.py` not edited (785 LOC cap, no growth)

## Notes

- STEP 6 is left `[/]` in `00-roadmap.md` — the executing agent does not
  mark `[x]`.
- Inbound `mcp_requests_received_total{method="list_tools"}` remains the
  **server** catalog PyPost exposes. Outbound discovery uses
  `mcp_client_*` names so the two must not be summed together.
- Empty URL is a WARNING + error counters, not a worker `run` and not an
  INFO success.
- Stale worker results (bumped generation) log DEBUG ignore and do not
  increment counters.
