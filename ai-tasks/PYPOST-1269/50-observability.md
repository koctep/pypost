# PYPOST-1269: Observability Implementation

## Logging Implementation

### Added Logs

Structured logging is maintained across both GUI desktop and headless daemon distribution modes:

- **EMERG**: N/A - Unused in Python standard logging hierarchy for PyPost runtimes.
- **ALERT**: N/A - Unused in standard logging hierarchy.
- **CRIT**: N/A - Critical runtime failures map to ERROR level lifecycle events with immediate non-zero exit codes.
- **ERR**:
  - `pypost/daemon.py:43`: `daemon_configuration_failed <error>` - CLI path resolution, directory validation, or initialization error before starting daemon runtime.
  - `pypost/core/qt/daemon_runtime.py:114`: `daemon_data_failed kind=<kind> category=<category> affected_server_id=<id>` - Strict snapshot failure emitted per affected MCP server.
  - `pypost/core/qt/daemon_runtime.py:150,153`: `daemon_start_failed <error>` - Strict config error or startup exception during initialization.
  - `pypost/core/qt/daemon_runtime.py:181`: `daemon_fatal reason=<reason>` - Fatal daemon lifecycle failure trigger (`startup_timeout`, `configuration`, `metrics_start_failed`, `metrics_<reason>`, `mcp_failed`, `mcp_stopped`) initiating clean termination.
  - `pypost/core/qt/daemon_runtime.py:197`: `daemon_mcp_shutdown_failed category=<category>` - Unhandled error during daemon MCP registry shutdown.
  - `pypost/core/qt/daemon_runtime.py:203`: `daemon_metrics_shutdown_failed category=<category>` - Unhandled error during daemon Prometheus metrics shutdown.
  - `pypost/main.py:174`: `agent_ui_attach_host_lifecycle action=start_failed endpoint=<endpoint> error=<category>` - Local AF_UNIX attach socket bind failure during GUI startup.
- **WARNING**:
  - `pypost/core/daemon_storage.py:95,113,150,167`: `daemon_storage_records_skipped kind=<kind> count=<count>` - Count-only diagnostic for unreferenced malformed collections/environments.
  - `pypost/core/metrics_server.py:205`: `metrics_server_non_localhost_bind host=<host> port=<port>` - Security warning when binding metrics outside 127.0.0.1.
  - `pypost/core/metrics_server.py:357,381`: `metrics_server_unexpected_exit` - Metrics server listener terminated unexpectedly.
- **NOTICE**: N/A - Mapped to standard INFO operational messages.
- **INFO**:
  - `pypost/main.py:157`: `app_startup` - GUI desktop application launch confirmation.
  - `pypost/main.py:82`: `log_level_applied level=<LEVEL>` - Configured logging level applied during app composition.
  - `pypost/main.py:88,96,109,116,119,125`: Subsystem instantiation events (`template_service_created`, `alert_manager_created`, `history_manager_created`, `storage_created`, `request_manager_created`, `mcp_manager_created`).
  - `pypost/main.py:167,184`: `agent_ui_attach_host_lifecycle action=start|stop endpoint=<endpoint>` - Agent UI attach host lifecycle in GUI mode.
  - `pypost/main.py:190`: `app_shutdown` - GUI desktop application graceful shutdown confirmation.
  - `pypost/core/qt/daemon_runtime.py:175`: `daemon_ready enabled_servers=<count>` - Daemon readiness confirmation when Prometheus listener and all enabled MCP instances are running.
  - `pypost/core/metrics_server.py:203,237,422`: Metrics server lifecycle (`Metrics server starting`, `metrics_server_listening host=<host> port=<port>`, `Metrics server stopped`).
- **DEBUG**:
  - `pypost/agent/attach_ipc.py:433`: `agent_ui_attach_ui_dispatch op=<op> widget_id=<id> in_current_tab=<bool>` - Agent attach IPC command dispatch in GUI desktop runtime (lines 432–438).

### Log Structure

Log format used:
- Structured logs: Yes (`event_name key=value` tokens throughout runtime entry points and lifecycles)
- Includes context: Yes (includes `level`, `endpoint`, `action`, `reason`, `kind`, `category`, `affected_server_id`, `enabled_servers`, `host`, `port`)
- Log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR` (`CRITICAL` mapped to fatal error handling with clean process termination)

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics:
- **Response time**:
  - `pypost_mcp_tool_call_duration_seconds` (Histogram) - MCP tool execution duration by method and status in `pypost/core/metrics_registry.py`.
  - `pypost_template_expression_render_duration_seconds` (Histogram) - Template variable expression evaluation latency.
  - *(Note: History I/O does not register a latency duration histogram; existing history I/O metrics are failure-oriented via `pypost_history_io_failures_total` Counter at `pypost/core/metrics_registry.py:157`).*
- **Throughput**:
  - `pypost_mcp_requests_total` (Counter) - Inbound MCP protocol requests partitioned by method.
  - `pypost_mcp_responses_total` (Counter) - Outbound MCP protocol responses partitioned by method and outcome.
  - `pypost_http_requests_sent_total` (Counter) - Outbound HTTP requests sent by method.
  - `pypost_http_responses_received_total` (Counter) - Inbound HTTP responses received by method and status code.
- **Error rate**:
  - `pypost_history_io_failures_total` (Counter) - History load and save failures partitioned by operation (`pypost/core/metrics_registry.py:157`).
  - `pypost_request_errors_total` (Counter) - Outbound HTTP request errors partitioned by category.
  - `pypost_template_expression_validation_failures_total` (Counter) - Expression syntax / validation errors by error code.
  - `pypost_environment_encryption_errors_total` (Counter) - Secret encryption / decryption errors by stage and reason.

### Business Metrics

Business metrics:
- `pypost_mcp_active_env_changes_total`: Number of active environment modifications invoked via MCP.
- `pypost_mcp_param_defaults_applied_total`: Number of default parameter values applied during MCP tool invocation.
- `pypost_hidden_value_masks_applied_total`: Sensitive credential masks applied in UI/logs.

### System Health Metrics

System health metrics:
- **Resource usage**: Exported via Prometheus default collectors:
  - `process_cpu_seconds_total` - CPU user and system time consumed.
  - `process_resident_memory_bytes` - Resident set memory footprint.
  - `process_open_fds` - Active open file descriptors and sockets.
- **Component status**:
  - `pypost_mcp_server_up` (Gauge) - Binary readiness status (1=ready, 0=down) for MCP server subsystem.
  - `pypost_mcp_server_instances` (Gauge) - Number of managed MCP servers partitioned by server type and lifecycle state (`running`, `stopped`, `failed`).

## Monitoring Integration

Integration with monitoring systems:
- [x] Prometheus metrics (Exposed via `/metrics` endpoint on HTTP server in both GUI and headless daemon runtimes)
- [x] Grafana dashboards (Standard Prometheus metrics export compatible with Prometheus/Grafana scrape targets)
- [x] Alerting rules (Alert on `daemon_fatal`, `pypost_mcp_server_up == 0`, and `agent_ui_attach_host_lifecycle action=start_failed`)
- [x] Log aggregation (ELK, Loki, syslog compatible structured standard error/output streams with `key=value` format)

## Validation Results

Validation results:
- [x] Logs are correctly formatted (Standard structured `event_name key=value` tokens)
- [x] Metrics are collected correctly (Both GUI and Daemon runtimes instantiate `MetricsManager` and expose `/metrics`)
- [x] Logging works in error scenarios (Validated in `test_daemon_cli.py`, `test_daemon_runtime.py`, and `test_daemon_config.py`)
- [x] Large data structures are not logged (Omitted sensitive payloads, bodies, and tokens; count-only summaries for skipped records)
- [x] Metrics are available for monitoring (Verified on HTTP `/metrics` port and MCP `metrics://all` resource)

## Notes

- **Dual Runtime Observability Parity**: Both GUI desktop runtime (`pypost` / `python -m pypost`) and headless daemon runtime (`pypost-daemon` / `python -m pypost.daemon`) share identical Prometheus metrics collectors and lifecycle reporting patterns.
- **Headless Error Isolation**: In headless daemon mode, error logging is directed to `sys.stderr` with structured tokens (`daemon_configuration_failed`, `daemon_fatal reason=...`), allowing systemd, Kubernetes, and container log drivers to ingest and parse error diagnostics cleanly.
- **Security & Privacy**: No sensitive tokens, decrypted passwords, request payload bodies, or internal file system paths beyond configured directories are emitted to standard logs.
