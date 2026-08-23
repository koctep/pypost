# PYPOST-1136: Observability Implementation

## Logging Implementation

### Added Logs

Structured key=value logging was added across the WebSocket session lifecycle and presentation layers:

- **ERR**:
  - `pypost.ui.presenters.websocket_presenter`: `websocket_handshake_failed session_id=%s category=%s detail_len=%d` — Emitted when connection establishment fails or handshake is rejected.
  - `pypost.core.qt.websocket_session`: `websocket_session_failed category=%s message=%s detail=%s` — Emitted on transport-level communication failure.
  - `pypost.core.qt.websocket_session`: `websocket_session_tls_validation_failed url=%s error=%s` — Emitted when TLS certificate verification fails.
- **WARNING**:
  - `pypost.ui.presenters.websocket_presenter`: `websocket_session_refused profile_id=%s reason=%s active=%d limit=%d` — Emitted when connection is refused because active sessions reach `ws_max_concurrent_sessions` or when lockdown mode (`0`) is active.
  - `pypost.ui.presenters.websocket_presenter`: `websocket_send_blocked_not_open state=%s` — Emitted when send message is attempted while connection is not open.
  - `pypost.core.qt.websocket_session`: `websocket_ephemeral_tls_exception_granted session_state=%s` — Emitted when user explicitly grants single-session TLS certificate trust.
  - `pypost.core.qt.websocket_session`: `websocket_tls_errors_encountered count=%d ignored=%s summary=%s` — Emitted when SSL error occurs during handshake.
  - `pypost.core.qt.websocket_transport`: `websocket_transport_ssl_errors_encountered count=%d errors=%s` — Emitted when Qt socket encounters SSL errors.
  - `pypost.core.qt.websocket_session`: `WebSocket heartbeat timeout expired (no pong response within %.1fs)` — Emitted on peer heartbeat timeout.
- **INFO**:
  - `pypost.ui.presenters.websocket_presenter`: `websocket_connect_initiated session_id=%s profile_id=%s url_masked=%s subprotocols=%d` — Emitted upon user clicking connect, with sanitized URL and subprotocol count.
  - `pypost.ui.presenters.websocket_presenter`: `websocket_connected session_id=%s subprotocol=%s handshake_ms=%d` — Emitted when session reaches `OPEN` state.
  - `pypost.ui.presenters.websocket_presenter`: `websocket_disconnect_initiated session_id=%s` — Emitted when user clicks disconnect or closes tab.
  - `pypost.ui.presenters.websocket_presenter`: `websocket_closed session_id=%s close_code=%d peer_initiated=%s duration_s=%d` — Emitted when session reaches `CLOSED` state.
  - `pypost.ui.presenters.websocket_presenter`: `websocket_presenter_teardown session_id=%s` — Emitted when presenter resources and slots are torn down.
  - `pypost.core.qt.websocket_session`: `websocket_ephemeral_tls_exception_revoked session_state=%s` — Emitted when ephemeral TLS trust is revoked.
  - `pypost.core.qt.websocket_session`: `Opening WebSocket session to %s ...` — Emitted when transport open begins with masked URL.
  - `pypost.core.qt.websocket_session`: `Scheduling WebSocket reconnect attempt %d/%d in %.1fs` — Emitted on automatic reconnect schedule.
- **DEBUG**:
  - `pypost.ui.presenters.websocket_presenter`: `websocket_sending_message length=%d` — Emitted when transmitting frame (payload length only, never content).
  - `pypost.core.websocket_session_policy`: `Evaluated state transition %s -> %s: valid=%s` — Emitted during state machine evaluation.
  - `pypost.core.qt.websocket_session`: `WebSocket session state transition: %s -> %s` — Emitted on session state change.
  - `pypost.core.qt.websocket_session`: `Starting WebSocket heartbeat timer (interval=%.1fs, timeout=%.1fs)` — Emitted when heartbeat loop starts.
  - `pypost.core.qt.websocket_session`: `WebSocket heartbeat ping triggered (payload_bytes=%d, timeout=%.1fs)` — Emitted on ping frame transmission.

### Log Structure

Log format used:
- Structured logs: Yes (`snake_case` event name followed by space-separated `key=value` pairs)
- Includes context: Yes (`session_id`, `profile_id`, `reason`, `active`, `limit`, `category`, `close_code`, `duration_s`)
- Log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- Secret Redaction Invariant: Query parameter secrets, passwords, bearer tokens, request headers, and message payloads are NEVER logged. All logged URLs are sanitized via `sanitize_text()`.

## Metrics Implementation

### Performance Metrics

Added performance and throughput metrics:
- **Throughput (messages)**: `websocket_messages_total{direction="inbound"|"outbound", kind="text"|"binary"|"ping"|"pong"}` — `pypost/core/metrics_registry.py:427`, `pypost/core/metrics_otel.py:234`
- **Throughput (bytes)**: `websocket_message_bytes_total{direction="inbound"|"outbound"}` — `pypost/core/metrics_registry.py:433`, `pypost/core/metrics_otel.py:238`
- **MCP Probe Latency**: `websocket_probe_duration_seconds{outcome="success"|"timeout"|"limit_reached"|"error"}` — `pypost/core/metrics_registry.py:462`, `pypost/core/metrics_otel.py:253`

### Business & Session Metrics

Business and session lifecycle metrics:
- `websocket_sessions_opened_total{outcome="success"|"failure"|"timeout"|"tls_rejected"}`: Counter tracking opened WebSocket sessions — `pypost/core/metrics_registry.py:415`, `pypost/core/metrics_otel.py:226`
- `websocket_sessions_closed_total{reason="clean"|"peer_close"|"heartbeat_timeout"|"transport_error"|"reconnect_exhausted"|"forced"}`: Counter tracking session closures — `pypost/core/metrics_registry.py:421`, `pypost/core/metrics_otel.py:230`
- `websocket_stream_entries_dropped_total{reason="capacity"|"memory_budget"}`: Counter tracking evicted stream entries due to bounded buffer limits — `pypost/core/metrics_registry.py:439`, `pypost/core/metrics_otel.py:242`
- `websocket_reconnect_attempts_total{outcome="scheduled"|"succeeded"|"exhausted"}`: Counter tracking automatic reconnection attempts — `pypost/core/metrics_registry.py:445`, `pypost/core/metrics_otel.py:246`
- `websocket_active_sessions`: Gauge tracking instantaneous active concurrent sessions holding concurrency slots — `pypost/core/metrics_registry.py:451`, `pypost/core/metrics_otel.py:431`
- `websocket_session_start_refused_total{reason="max_concurrent"|"disabled"}`: Counter tracking refused session connections due to concurrency ceiling or lockdown policy — `pypost/core/metrics_registry.py:456`, `pypost/core/metrics_otel.py:249`

### System Health & Concurrency Ceiling Metrics

System concurrency governance metrics:
- **Active Connections Gauge**: `websocket_active_sessions` updated in real time upon slot acquisition and release in `SessionSlots` and `WebSocketPresenter`.
- **Refusal Counter**: `websocket_session_start_refused_total` incremented with discrete reason labels (`max_concurrent` or `disabled`) when process-wide session limit is saturated or zeroed.

## Monitoring Integration

Integration with monitoring systems:
- [x] Prometheus metrics (exposed via `/metrics` endpoint on port 9080)
- [x] OpenTelemetry instruments (Meter counters, gauge tracker, and histogram in `pypost/core/metrics_otel.py`)
- [x] Dynamic MetricsManager delegation (GUI thread and worker thread safety via `pypost/core/qt/metrics.py`)
- [x] Documentation in `doc/prometheus_monitoring.md` updated with full 9-instrument inventory table (44 total registered instruments)
- [x] Documentation in `doc/dev/logging.md` updated with WebSocket events and secret masking policy

## Validation Results

Validation results:
- [x] Logs are correctly formatted: All WebSocket logs use `snake_case` event names and space-separated `key=value` pairs.
- [x] Metrics are collected correctly: Tested via `TestWebSocketPrometheusMetrics` scraping `generate_latest()` output.
- [x] Logging works in error scenarios: Handshake failure, connection refusal, lockdown mode, TLS errors, and teardowns verified in `tests/test_websocket_settings_and_limits_repro.py`.
- [x] Large data structures and secrets are not logged: Payloads are logged by byte length only; URLs are sanitized; headers and secret tokens never appear in logs (verified with `caplog`).
- [x] Metrics are available for monitoring: Scrapable on Prometheus `/metrics` and OTel meter provider.
- [x] All 211 `test_websocket*` unit/integration tests pass with 0 failures.
- [x] `scripts/audit_baseline_metrics.py --check` passes without architectural violations or LOC drift.

## Notes

- Concurrency slots are managed by the thread-safe `SessionSlots` coordinator in `pypost/core/websocket_session_policy.py`.
- Slot release is guaranteed across all terminal transitions (`CLOSED`, `FAILED`, user disconnect, server disconnect, exception, and UI teardown).
- Setting `ws_max_concurrent_sessions = 0` locks down WebSocket connectivity across the entire application runtime with `websocket_session_start_refused_total{reason="disabled"}` incremented.
