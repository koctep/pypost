# PYPOST-1150: Observability Implementation

## Logging Implementation

### Added Logs

This task focuses on test-contract hardening and protocol conformance verification for `MetricsTrackerProtocol`, `MetricsManager`, `NullMetrics`, and `OtelMetricsTracker`. The underlying components (`MetricsServer`, `MetricsManager`, `OtelMetricsTracker`, and `MetricsRegistry`) already feature comprehensive operational logging and telemetry instrumentation.

Existing logging across the metrics tracking and server layer:
- **EMERG**: N/A — No emergency shutdown logs required at this application layer.
- **ALERT**: N/A — No operational alert logs required at this layer.
- **CRIT**: N/A — Unhandled exceptions are trapped and handled gracefully without crashing host process.
- **ERR**: `pypost/core/metrics_server.py` (`_notify_start_failed`, `_run_uvicorn`):
  - `logger.error("metrics_server_start_failed host=%s port=%d message=%s", host, port, message)`: Triggered on port bind collisions (`EADDRINUSE`) or server startup failures.
  - `logger.exception("metrics_server_start_failed")`: Captures unexpected startup exceptions with traceback context before notifying listeners via `MetricsManager.start_failed` signal.
- **WARNING**: `pypost/core/metrics_server.py` (`start_server`):
  - `logger.warning("metrics_server_non_localhost_bind host=%s port=%d — metrics and MCP resources are exposed without authentication", host, port)`: Emitted when binding to an external/non-localhost interface (`0.0.0.0`, external IPs) alerting operators to unauthenticated network exposure.
- **NOTICE**: N/A — Syslog NOTICE level not utilized in this component.
- **INFO**: `pypost/core/metrics_server.py` (`start_server`, `_notify_started`):
  - `logger.info("Metrics server starting on %s:%d", host, port)`: Emitted upon thread launch.
  - `logger.info("metrics_server_listening host=%s port=%d", host, port)`: Emitted once uvicorn server successfully completes socket bind and begins listening.
- **DEBUG**: N/A — Verbose debug logs are avoided in favor of high-throughput Prometheus/OTel counters.

### Log Structure

Log format used:
- Structured logs: Yes (`key=value` paired attributes in message strings for machine parseability)
- Includes context: Yes (`host`, `port`, `message`, formatted bind errors, exception tracebacks)
- Log levels: INFO, WARNING, ERROR

### Sensitive Data & Privacy Audit

A comprehensive review of `MetricsTrackerProtocol`, `NullMetrics`, `MetricsManager`, and `OtelMetricsTracker` confirms strict adherence to privacy and secret-handling principles:
1. **No Sensitive Payloads in Signatures**: None of the 44 tracking methods accept authorization tokens, bearer headers, passwords, encryption keys, decrypted values, or full HTTP payload bodies.
2. **Masking & Encryption Observability**: Methods such as `track_hidden_value_mask_applied(surface: str)` and `track_environment_value_encryption()` / `track_environment_value_decryption()` record only invocation counts. The plaintext secret contents and ciphertext tokens are never passed or logged.
3. **Truncation & Error Categorization**: HTTP body truncation tracks only `method` (`track_response_body_truncated(method: str)`). Request errors record only high-level categorizations via `ErrorCategory` enum (`NETWORK`, `TIMEOUT`, `PROTOCOL`, etc.), ensuring zero leak of sensitive response or request bodies.
4. **Safe Default (`NullMetrics`)**: When running in headless mode, unit tests, or environments without telemetry configured, `NullMetrics` acts as a zero-overhead, silent no-op sink with no logging or data accumulation.

---

## Metrics Implementation (if applicable)

The metrics layer defines 44 tracking methods spanning GUI actions, HTTP lifecycle, MCP tool interactions, template evaluation, environment encryption, and WebSocket sessions.

### Performance Metrics

Added and verified performance metrics:
- **Response time / Latencies**:
  - `mcp_tool_call_duration_seconds` (Histogram): Execution duration of MCP tool calls, partitioned by `method` and `status` (`pypost/core/metrics_registry.py`, `pypost/core/metrics_otel.py`).
  - `template_expression_render_duration_seconds` (Histogram): Duration of Jinja/template expression evaluations, partitioned by `render_path` (`pypost/core/metrics_registry.py`, `pypost/core/metrics_otel.py`).
  - `websocket_probe_duration_seconds` (Histogram): Latency of WebSocket connection probe handshakes, partitioned by `outcome` (`pypost/core/metrics_registry.py`, `pypost/core/metrics_otel.py`).
- **Throughput**:
  - `requests_sent_total` (Counter): Volume of HTTP client requests initiated, partitioned by `method`.
  - `responses_received_total` (Counter): Volume of HTTP client responses, partitioned by `method` and `status_code`.
  - `websocket_messages_total` (Counter): WebSocket message throughput, partitioned by `direction` (`inbound`, `outbound`) and `kind` (`text`, `binary`).
  - `websocket_message_bytes_total` (Counter): WebSocket network traffic volume in bytes, partitioned by `direction`.
  - `mcp_requests_total` / `mcp_responses_total` (Counter): Inbound and outbound MCP protocol traffic volume.
- **Error rate**:
  - `request_errors_total` (Counter): HTTP failure frequency, partitioned by `category` (`ErrorCategory`).
  - `request_retries_total` (Counter): Transient failure retries, partitioned by `method` and `status_category`.
  - `request_retries_exhausted_total` (Counter): Permanent request failures due to retry limit exhaustion, partitioned by `endpoint`.
  - `template_expression_validation_failures_total` (Counter): Syntax or validation failures during template parsing, partitioned by `render_path`, `code`, and `function_name`.
  - `variable_validation_failures_total` (Counter): Variable format and resolution failures, partitioned by `reason`.
  - `environment_encryption_errors_total` (Counter): Cryptographic operation failures, partitioned by `stage` and `reason`.
  - `websocket_stream_entries_dropped_total` (Counter): Frame drop events, partitioned by `reason`.
  - `websocket_session_start_refused_total` (Counter): Session connection rejections, partitioned by `reason`.

### Business Metrics

Business and user workflow metrics:
- `gui_send_clicks_total`: Frequency of primary "Send" button actions executed in UI.
- `gui_save_actions_total` / `gui_save_as_actions_total`: User request persistence events, partitioned by `source`.
- `gui_new_tab_actions_total`: New tab creation events, partitioned by `source` and `protocol` (`http`, `ws`, `mcp`, `unknown`).
- `gui_copy_curl_action_total`: Frequency of user copying request as cURL command.
- `gui_collection_delete_actions_total` / `gui_collection_rename_actions_total`: Collection management actions, partitioned by `item_type` and `status`.
- `gui_response_search_actions_total`: Response search actions, partitioned by `source` and `has_matches`.
- `gui_method_body_autoswitch_total`: Automatic request body switching events based on HTTP method.
- `history_entries_appended_total` / `history_load_into_editor_total`: Request history usage tracking.
- `environment_value_encryptions_total` / `environment_value_decryptions_total`: Volume of encrypted environment variable usage.

### System Health Metrics

System health and component lifecycle indicators:
- **Resource usage**:
  - `response_body_truncated_total`: Count of oversized response bodies truncated to prevent memory exhaustion, partitioned by `method`.
  - `websocket_message_bytes_total`: Ingress and egress byte volume monitoring memory and network utilization.
- **Component status**:
  - `mcp_server_up` (Gauge: `1` = ready, `0` = idle): Readiness state of the embedded MCP tool server.
  - `mcp_server_instances` (Observable Gauge): Instantaneous count of configured MCP server instances by state (`stopped`, `starting`, `running`, `failed`).
  - `websocket_active_sessions` (Observable Gauge): Instantaneous count of active concurrent WebSocket sessions.

---

## Monitoring Integration

Integration with monitoring systems:
- [x] Prometheus metrics: Native Prometheus registry exposed via ASGI endpoint (`/metrics`) and MCP resource (`metrics://all`) in `pypost/core/metrics_server.py`.
- [x] OpenTelemetry metrics: Native OTel meters, counters, histograms, and observable gauges supported via `OtelMetricsTracker` (`pypost/core/metrics_otel.py`).
- [ ] Grafana dashboards: Visualizations deployed via operational monitoring infrastructure.
- [ ] Alerting rules: Prometheus alert rules configured on error rate counters and server readiness gauges.
- [x] Log aggregation: Structured key=value logs emitted to standard error for consumption by journald, Docker daemon, or vector/loki collectors.

---

## Validation Results

Validation results:
- [x] Logs are correctly formatted (structured key=value format for server lifecycle and bind diagnostics).
- [x] Metrics are collected correctly (all 44 tracking methods defined on `MetricsTrackerProtocol` are implemented and verified across `MetricsManager` and `OtelMetricsTracker`).
- [x] Logging works in error scenarios (bind conflict detection, non-localhost security warnings, unhandled startup exceptions).
- [x] Large data structures are not logged (all methods pass scalar parameters or enums; no request/response bodies or secrets logged).
- [x] Metrics are available for monitoring (available via Prometheus scrape `/metrics`, MCP resource `metrics://all`, and OpenTelemetry SDK).

---

## Notes

- **Automated Protocol Parity Contract**: In `tests/test_metrics_protocol.py`, reflection-based test functions (`_get_protocol_methods` and `_assert_tracker_satisfies_all_protocol_methods`) continuously enforce that any method added to `MetricsTrackerProtocol` is implemented with exact signature parity on `MetricsManager`, `NullMetrics`, and `OtelMetricsTracker`.
- **Zero-Failure Execution on Null Object**: `test_null_metrics_all_methods_callable_without_error` dynamically invokes all 44 protocol methods on `NullMetrics` with dummy typed arguments, ensuring headless or test environments cannot trigger runtime `AttributeError` or `TypeError` exceptions.
