# PYPOST-1464: Observability Implementation

## Logging Implementation

### Added Logs

Isolated proxy startup parity reuses the existing structured `key=value` lifecycle logs in
`MCPServerRegistry`, `ProcessServerRunner`, `McpProcessSupervisor`, and `MCPProxyServerImpl`
without adding new log statements or exposing credentials:

- **EMERG**: N/A — isolated proxy lifecycle and upstream transport errors stay contained within the
  owning worker or host instance.
- **ALERT**: N/A — per-instance proxy failures do not affect neighboring servers.
- **CRIT**: N/A — startup and upstream failures report recoverable `failed` status or MCP protocol
  errors.
- **ERR**:
  - `pypost/core/mcp_server_runner.py` (`ProcessServerRunner.start`):
    `mcp_process_runner_start_failed instance_id=%s error=%s` — logs only the exception class name.
  - `pypost/core/mcp_process_supervisor.py` (`_apply_ipc_message`, `_monitor_loop`):
    `mcp_worker_start_failed` and `mcp_worker_unexpected_exit` — child startup or runtime exit.
  - `pypost/core/mcp_proxy_server_impl.py` (`_record_proxy_failure`):
    `mcp_proxy_<operation>_<error|timeout|connect_error> proxy=%s duration_ms=%.2f` — sanitized
    operation failure diagnostics inside the worker.
- **WARNING**:
  - `pypost/core/mcp_proxy_server_impl.py` (`_resolve_headers`):
    `mcp_proxy_unresolved_variable proxy=%s variable=%s header=%s` — logs variable and header names
    only, never values.
  - `pypost/core/mcp_server_registry.py` (`_reconfigure_process`):
    `mcp_registry_process_reconfigure_rejected` — records candidate rejection and restoration
    without exception text or configuration payloads.
- **NOTICE**: N/A — operational lifecycle transitions use `INFO` under the project logging mapping.
- **INFO**:
  - `pypost/core/mcp_process_supervisor.py` (`spawn_worker`, `_apply_ipc_message`, `stop_worker`):
    `mcp_worker_spawned instance_id=%s pid=%s host=%s port=%d tool_count=%d`,
    `mcp_worker_started instance_id=%s pid=%s`, `mcp_worker_stop_requested`, and
    `mcp_worker_stop_finished`.
  - `pypost/core/mcp_server_registry.py` (`start`, `_reconfigure_process`, `_set_status`):
    `mcp_registry_start_requested`, `mcp_registry_process_reconfigured`, and `mcp_registry_status`.
  - `pypost/core/mcp_proxy_server_impl.py` (`_log_proxy_success`):
    `mcp_proxy_list_tools_success`, `mcp_proxy_call_tool_completed`, and peer operation completion
    events with counts and durations only.
- **DEBUG**:
  - `pypost/core/mcp_proxy_server_impl.py` (`_connect_upstream`, `_dispatch_proxy_operation`):
    `mcp_proxy_connecting_upstream proxy=%s transport=%s header_keys=%s timeout=%.1f` and
    `mcp_proxy_operation_started` — logs header keys only via `sanitize_proxy_headers`, omitting
    `upstream_url` and header values.

### Log Structure

Log format used:
- Structured logs: yes (`event_name key=value`)
- Includes context: yes (`instance_id`, `pid`, `host`, `port`, `proxy`, `operation`, `duration_ms`;
  never `START` payloads, `upstream_url`, header values, or variable snapshots)
- Log levels: DEBUG, INFO, WARNING, ERROR (ERR)

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Response time**: `MCPProxyServerImpl._dispatch_proxy_operation` records tool call latency via
  `track_mcp_tool_call_duration("POST", outcome, duration_s)` in `pypost/core/mcp_proxy_server_impl.py`.
- **Throughput**: `track_mcp_request_received("POST")` and `track_mcp_response_sent("POST", outcome)`
  in `pypost/core/mcp_proxy_server_impl.py`.
- **Error rate**: tracked via `outcome="error"` in `track_mcp_response_sent` and registry `failed`
  instance state counts.

### Business Metrics

Business metrics:
- `mcp_server_instances{state}`: updated by `MCPServerRegistry._publish_instance_metrics` via
  `set_mcp_server_instance_counts` on every proxy start, stop, reconfiguration, and failure state
  transition in `pypost/core/mcp_server_registry.py`.

### System Health Metrics

System health metrics:
- **Resource usage**: N/A — no new process resource collectors required for proxy startup parity.
- **Component status**: `starting`, `running`, `failed`, and `stopped` states published for
  isolated proxy servers through `MCPServerRegistry`.

## Monitoring Integration

Integration with monitoring systems:
- [x] Prometheus metrics (existing `mcp_server_instances` gauge and MCP request/duration trackers)
- [ ] Grafana dashboards (no new dashboard panels required)
- [ ] Alerting rules (existing failure state and error log patterns apply)
- [x] Log aggregation (structured `key=value` events without sensitive fields)

## Validation Results

Validation results:
- [x] Logs are correctly formatted (`mcp_worker_spawned`, `mcp_worker_started`, and
  `mcp_registry_process_reconfigured` verified via `caplog`)
- [x] Metrics are collected correctly (existing registry state and proxy operation trackers remain
  active)
- [x] Logging works in error scenarios (`ProcessServerRunner.start` and supervisor error paths log
  exception types/categories without leaking secrets)
- [x] Large data structures are not logged (`START` payloads, `upstream_url`, resolved bearer
  tokens, and variable snapshots are absent from `caplog.text`)
- [x] Metrics are available for monitoring (registry status transitions publish instance counts)

## Notes

`tests/test_mcp_process_proxy_repro.py` asserts via `caplog` that starting, invoking, and
reconfiguring an isolated proxy emits the expected supervisor and registry lifecycle events while
excluding upstream URLs and resolved secret token values from captured logs.
