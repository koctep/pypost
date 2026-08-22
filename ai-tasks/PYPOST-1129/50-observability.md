# PYPOST-1129: Observability Implementation

## Overview

PYPOST-1129 implements `ScriptedWebSocketServer` and the `ws_test_server` fixture in `tests/websocket_echo_server.py` as an offline, in-process WebSocket test server for PyPost WebSocket client feature testing.

Observability for this test utility is structured across three layers:
1. **Diagnostic Properties**: Real-time state inspection for tests and test assertion helpers (`is_listening`, `host`, `port`, `url`, `behavior`, `clients`, `connected_clients`).
2. **In-Memory Metrics & Tracking Counters**: Cumulative lifecycle counters and ordered frame buffers (`connection_count`, `disconnection_count`, `received_messages`, `received_text_messages`, `received_binary_messages`, `sent_messages`, `sent_text_messages`, `sent_binary_messages`) reset via `.reset()`.
3. **Structured Debug Logging**: Plaintext `key=value` debug events adhering to PyPost project conventions (`doc/dev/logging.md`) emitted through the `tests.websocket_echo_server` logger without logging large message payloads.

## Logging Implementation

### Added Logs

Structured logs added to `tests/websocket_echo_server.py`:
- **EMERG**: N/A — In-process test utility; no emergency kernel/system alerts.
- **ALERT**: N/A — No operational alerting required.
- **CRIT**: N/A — Critical errors are surfaced as exceptions (`RuntimeError`).
- **ERR**: N/A — Server startup failures raise `RuntimeError(f"Failed to start QWebSocketServer: {errorString}")`.
- **WARNING**: N/A — Scripted rejections (CORS, close codes) are intentional test actions and logged at DEBUG.
- **NOTICE**: N/A — PyPost convention maps significant informational events to INFO/DEBUG.
- **INFO**: N/A — Test utility uses DEBUG level to avoid test output and CI log pollution.
- **DEBUG**:
  - `ws_server_started`: `tests/websocket_echo_server.py:start` — `name=%s host=%s port=%d url=%s`
  - `ws_server_stopped`: `tests/websocket_echo_server.py:stop` — `name=%s`
  - `ws_server_reset`: `tests/websocket_echo_server.py:reset` — `name=%s`
  - `ws_server_configured`: `tests/websocket_echo_server.py:configure` — `name=%s behavior=%s`
  - `ws_server_origin_auth_evaluated`: `tests/websocket_echo_server.py:_on_origin_auth_required` — `name=%s allowed=%s behavior=%s`
  - `ws_server_client_connected`: `tests/websocket_echo_server.py:_on_new_connection` — `name=%s client_count=%d total_connections=%d`
  - `ws_server_client_disconnected`: `tests/websocket_echo_server.py:_on_client_disconnected` — `name=%s remaining_clients=%d total_disconnections=%d`
  - `ws_server_text_message_received`: `tests/websocket_echo_server.py:_on_text_message_received` — `name=%s length=%d total_received=%d`
  - `ws_server_binary_message_received`: `tests/websocket_echo_server.py:_on_binary_message_received` — `name=%s length=%d total_received=%d`
  - `ws_server_text_message_sent`: `tests/websocket_echo_server.py:_send_client_text` — `name=%s length=%d total_sent=%d`
  - `ws_server_binary_message_sent`: `tests/websocket_echo_server.py:_send_client_binary` — `name=%s length=%d total_sent=%d`
  - `ws_server_flood_emitted`: `tests/websocket_echo_server.py:flood` — `name=%s count=%d size=%d`
  - `ws_server_clients_dropped`: `tests/websocket_echo_server.py:drop_clients` — `name=%s count=%d`

### Log Structure

Log format used:
- Structured logs: **Yes** — Space-separated `key=value` pairs with snake_case event names.
- Includes context: **Yes** — Includes server name, host/port/URL, client counts, frame sizes, and cumulative sequence counters.
- Log levels: **DEBUG** (clean offscreen testing and CI guardrail compatibility).

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics for test observability:
- **Response time**: Event loop tick duration measured during offscreen event polling (`max_tick_duration_ms < 50.0ms` verified in `test_offscreen_responsiveness_under_load`).
- **Throughput**: Message burst count and frame sizing tracking (`flood(count, size)` emits structured counts and logs metrics).
- **Error rate**: Disconnection and handshake rejection counters tracked deterministically.

### Business & Test Utility Metrics

Test observability counters and buffers:
- `connection_count`: Total accepted client connections since server startup or `.reset()` (`tests/websocket_echo_server.py:ScriptedWebSocketServer.connection_count`).
- `disconnection_count`: Total client disconnections since server startup or `.reset()` (`tests/websocket_echo_server.py:ScriptedWebSocketServer.disconnection_count`).
- `received_messages`: Ordered sequence of all incoming text and binary frames (`tests/websocket_echo_server.py:ScriptedWebSocketServer.received_messages`).
- `received_text_messages`: Filtered text frames received (`tests/websocket_echo_server.py:ScriptedWebSocketServer.received_text_messages`).
- `received_binary_messages`: Filtered binary frames received (`tests/websocket_echo_server.py:ScriptedWebSocketServer.received_binary_messages`).
- `sent_messages`: Ordered sequence of all emitted text and binary frames (`tests/websocket_echo_server.py:ScriptedWebSocketServer.sent_messages`).
- `sent_text_messages`: Filtered text frames emitted (`tests/websocket_echo_server.py:ScriptedWebSocketServer.sent_text_messages`).
- `sent_binary_messages`: Filtered binary frames emitted (`tests/websocket_echo_server.py:ScriptedWebSocketServer.sent_binary_messages`).

### System Health Metrics

System health metrics:
- **Resource usage**: Zero socket/port leaks across repeated startup/teardown cycles verified in `test_repeated_startup_teardown_leak_free`.
- **Component status**: `is_listening` boolean property exposing underlying `QWebSocketServer` listen state.

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics (N/A — test utility infrastructure)
- [ ] Grafana dashboards (N/A — test utility infrastructure)
- [ ] Alerting rules (N/A — test utility infrastructure)
- [x] Pytest log capture and caplog inspection (`pytest --log-file`, `caplog.at_level`)
- [x] CI test log guardrails verified (`scripts/verify_test_log_guardrails.py`)

## Validation Results

Validation results:
- [x] Logs are correctly formatted (standardized `key=value` format with `%` interpolation).
- [x] Metrics and counters are collected correctly (`test_observability_counters_and_buffers` PASSED).
- [x] Structured debug logging is verified via pytest caplog (`test_observability_structured_logging` PASSED).
- [x] Logging works in error/rejection scenarios (`test_behavior_reject_handshake`, `test_behavior_subprotocol_refuse`, `test_behavior_close_with_code_and_reason`).
- [x] Large data structures are not logged (message payloads are represented by `length=%d` in log records, preventing log bloat).
- [x] Test suite passing: 17/17 tests in `tests/test_websocket_echo_server.py`.
- [x] Static analysis: flake8 clean, mypy baseline clean.

## Notes

- All logging uses standard Python `logging.getLogger(__name__)`.
- Server uses ephemeral loopback binding (`127.0.0.1:0`) and deterministic bounded waits via `wait_until()` to ensure reliable test execution without arbitrary sleep delays.
