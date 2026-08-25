# PYPOST-1173: Observability Implementation

## Logging Implementation

### Added Logs

Describe added logging:

- **EMERG**: none — no system-failure path in this wiring-only change
- **ALERT**: none
- **CRIT**: none
- **ERR**: none added — existing MCP failure logs already cover this path
  (`mcp_operation_timeout`, `mcp_operation_failed` in
  `pypost/core/mcp_client_service.py`; `request_execution_failed` in
  `pypost/core/request_service.py`)
- **WARNING**: none
- **NOTICE**: none
- **INFO**: none — per-request header forwarding is high-frequency
- **DEBUG**: `MCPClientService.run` (`pypost/core/mcp_client_service.py`) —
  `mcp_operation_start` now includes `header_count=%d` (length of the resolved
  outbound header map, or `0` when `headers` is `None` or empty). Header
  **values** and **keys** are not logged (Bearer tokens / API keys).

Existing logs kept (not new, still sufficient for success/error):

- **DEBUG** `mcp_operation_success` — `url`, `operation`, `elapsed`
- **ERR** `mcp_operation_timeout` / `mcp_operation_failed` — `url`,
  `operation`, `category`/`timeout`, `detail` (exception text only; no headers)
- **ERR** `request_execution_failed` — `method`, `url`, `category`, `detail`

`RequestService._execute_mcp` has no new log. The client start event is the
point where headers are attached to the Streamable HTTP client. Duplicating
count at the request-service layer would add noise without extra diagnosis.

### Log Structure

Log format used:

- Structured logs: yes (event name + key=value fields, matching existing MCP
  client events)
- Includes context: yes (`url`, `operation`, `header_count`)
- Log levels: DEBUG (start/success), ERROR (timeout/failure) — unchanged set;
  only the start event gained `header_count`

## Metrics Implementation (if applicable)

No new metrics. Architecture (`20-architecture.md`) does not require a counter
for this debt ticket. Existing MCP Send metrics already fire:

- `RequestService._execute_mcp` — `track_request_sent(request.method)`
- `RequestService._execute_mcp` — `track_response_received(method, status)`
- `RequestService.execute` — `track_request_error(category)` on `ExecutionError`

Those already distinguish method MCP via the `method` label. Header forwarding
is a boolean wiring property, not a throughput dimension.

### Performance Metrics

Added performance metrics:

- **Response time**: none new — existing `mcp_operation_success elapsed`
  DEBUG log and `ResponseData.elapsed_time`
- **Throughput**: none new — existing `track_request_sent` /
  `track_response_received`
- **Error rate**: none new — existing `track_request_error` and ERROR logs

### Business Metrics

Business metrics:

- none added — sending resolved headers is auth parity, not a conversion event

### System Health Metrics

System health metrics:

- **Resource usage**: CPU, memory, disk — unchanged; not in scope
- **Component status**: MCP client remains covered by existing ERROR logs on
  timeout / network / unknown failure

## Monitoring Integration

Integration with monitoring systems:

- [ ] Prometheus metrics — no new series; existing request counters apply
- [ ] Grafana dashboards — no new dashboard
- [ ] Alerting rules — no new alerts (header drop is a wiring defect, not a
  runtime signal)
- [x] Log aggregation (ELK, Loki, etc.) — same logger
  `pypost.core.mcp_client_service`; new field is `header_count` on
  `mcp_operation_start`

`doc/dev/logging.md` still lists `mcp_operation_start` fields as `url`,
`operation`. Updating that catalog is Step 8 (dev docs), not this step.

## Validation Results

Validation results:

- [x] Logs are correctly formatted (`event field=value`, syslog-style DEBUG)
- [x] Metrics are collected correctly (unchanged MCP Send counters)
- [x] Logging works in error scenarios (existing ERROR logs; no header dump)
- [x] Large data structures are not logged (count only, never the header map)
- [x] Metrics are available for monitoring (pre-existing request metrics)
- [x] Header values never appear in logs (unit tests:
  `test_run_logs_header_count_not_values`,
  `test_run_logs_zero_header_count_when_headers_omitted`)

## Notes

- Auth headers must never be logged in full. This step logs **count** only,
  not keys or values. The proxy pattern (`header_keys=%s` in
  `mcp_proxy_server_impl.py`) is more verbose; count is enough to confirm
  that `_execute_mcp` forwarded a non-empty map versus an empty one (FR-2).
- STEP 6 is left `[/]` in `00-roadmap.md` — the executing agent does not mark
  its own step `[x]`.
