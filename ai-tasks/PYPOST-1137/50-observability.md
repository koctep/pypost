# PYPOST-1137: Observability Implementation

## Logging Implementation

### Added Logs

Structured logging is implemented across `pypost/core/qt/websocket_probe_runner.py` and `pypost/core/websocket_mcp_tools.py` covering the complete lifecycle of bounded WebSocket MCP probes:

- **EMERG**: None (not applicable for user-space client probes).
- **ALERT**: None (not applicable for user-space client probes).
- **CRIT**: None (not applicable for user-space client probes).
- **ERR**:
  - `pypost/core/websocket_mcp_tools.py` (`execute_websocket_probe`): `execute_websocket_probe_failed tool=%s reason=no_result` when the runner thread exits without producing a result.
- **WARNING**:
  - `pypost/core/qt/websocket_probe_runner.py` (`WebSocketProbeRunner.run`): `websocket_probe_refused probe_id=%s active_count=%d limit=%d reason=%s` when session concurrency slots are exhausted.
  - `pypost/core/qt/websocket_probe_runner.py` (`_ProbeTransportListener.on_failed`): `websocket_probe_failed probe_id=%s category=%s message=%s` on transport or socket connection errors.
  - `pypost/core/qt/websocket_probe_runner.py` (`_ProbeTransportListener.on_tls_errors`): `websocket_probe_tls_errors probe_id=%s error=%s` on TLS certificate verification errors.
  - `pypost/core/qt/websocket_probe_runner.py` (`_on_deadline`): `websocket_probe_timeout probe_id=%s max_duration_ms=%d` when the hard-deadline timer trips and aborts the probe.
- **NOTICE**: None.
- **INFO**:
  - `pypost/core/websocket_mcp_tools.py` (`execute_websocket_probe`): `execute_websocket_probe_started tool=%s eff_msgs=%d eff_dur_ms=%d has_stop_when=%s has_preset=%s arg_count=%d` on tool invocation dispatch.
  - `pypost/core/websocket_mcp_tools.py` (`execute_websocket_probe`): `execute_websocket_probe_completed tool=%s outcome=%s duration_ms=%.1f messages_received=%d close_code=%s` on probe completion and transcript generation.
  - `pypost/core/qt/websocket_probe_runner.py` (`WebSocketProbeRunner.run`): `websocket_probe_started probe_id=%s max_messages=%d max_duration_ms=%d has_stop_when=%s has_initial_payload=%s` on runner thread initialization.
  - `pypost/core/qt/websocket_probe_runner.py` (`_ProbeTransportListener.on_text`, `on_binary`): `websocket_probe_stop_condition_triggered probe_id=%s outcome=%s messages_count=%d` when stopping conditions (`max_messages` or `stop_when`) are satisfied.
  - `pypost/core/qt/websocket_probe_runner.py` (`WebSocketProbeRunner.run` finally): `websocket_probe_finished probe_id=%s outcome=%s duration_ms=%.1f messages_received=%d slot_released=true` on runner thread completion and slot cleanup.
- **DEBUG**:
  - `pypost/core/qt/websocket_probe_runner.py` (`_ProbeTransportListener.on_opened`): `websocket_probe_opened probe_id=%s subprotocol=%s` on successful WebSocket handshake.
  - `pypost/core/qt/websocket_probe_runner.py` (`_ProbeTransportListener.on_opened`): `websocket_probe_initial_payload_sent probe_id=%s bytes=%d` when initial preset payload is transmitted.
  - `pypost/core/qt/websocket_probe_runner.py` (`_ProbeTransportListener.on_text`, `on_binary`): `websocket_probe_frame_received probe_id=%s kind=%s bytes=%d count=%d` on every incoming frame.
  - `pypost/core/qt/websocket_probe_runner.py` (`_ProbeTransportListener.on_closed`): `websocket_probe_closed probe_id=%s code=%d reason=%s peer_initiated=%s` on connection close handshake.

### Log Structure

Log format used:
- **Structured logs**: Yes (key-value formatted parameters in log messages).
- **Includes context**: Yes (probe IDs, tool names, message counts, byte sizes, outcomes, error categories, and durations).
- **Log levels**: `DEBUG`, `INFO`, `WARNING`, `ERROR`.
- **Secret Redaction**: Sensitive parameter values, query credentials, and payload bodies are strictly excluded from log statements (only byte counts and sanitized metadata are emitted). Output transcripts are sanitized via `McpResponseSanitizer.sanitize_text`.

## Metrics Implementation

### Performance Metrics

Added performance metrics:
- **Response time**: `websocket_probe_duration_seconds{outcome}` (Histogram) - `pypost/core/metrics_registry.py` / `pypost/core/metrics_otel.py` / `pypost/core/websocket_mcp_tools.py` (tracks duration of probe executions labeled by outcome: `success`, `limit_reached`, `stop_when_matched`, `timeout`, `error`, `refused`).

### Business Metrics

- `mcp_requests_received_total{method}`: Counter tracking total incoming MCP tool calls.
- `mcp_responses_sent_total{method, status}`: Counter tracking MCP tool responses sent.
- `McpActivityLog` audit entries: Every probe execution records a structured `McpActivityEntry.new_call_tool` entry containing tool name, outcome, argument count, error detail, and execution duration in milliseconds.

### System Health Metrics

System health metrics:
- **Active WebSocket Sessions**: `websocket_active_sessions` (Gauge) - tracks instantaneous concurrent sessions managed by `SessionSlots`.
- **Session Refusals**: `websocket_session_start_refused_total{reason}` (Counter) - tracks refused probe connection attempts due to concurrency limits (`max_concurrent`).

## Monitoring Integration

Integration with monitoring systems:
- [x] Prometheus metrics (`websocket_probe_duration_seconds`, `websocket_active_sessions`, `websocket_session_start_refused_total`)
- [x] OpenTelemetry bridge support (`pypost/core/metrics_otel.py`)
- [x] In-app MCP Activity Log (`McpActivityLog`)
- [x] Standard library `logging` compatible with syslog / journald / ELK / Loki log aggregators

## Validation Results

Validation results:
- [x] Logs are correctly formatted with key-value pairs
- [x] Metrics are collected correctly and registered in both Prometheus and OTel registries
- [x] Logging works in all error scenarios (transport errors, timeouts, TLS errors, slot refusals)
- [x] Large data structures and message payload contents are not logged (only byte counts and sanitized metadata)
- [x] Metrics are available for monitoring and validated by automated tests (`tests/test_websocket_mcp_probe_repro.py`)

## Notes

- All secrets and environment variables are masked in returned transcripts using `McpResponseSanitizer.sanitize_text` before returning tool results to agents.
- Runner thread cleanup and slot release are guaranteed via `finally` blocks in `WebSocketProbeRunner.run()`.
