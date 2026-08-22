# PYPOST-1127: Observability Implementation

## Logging Implementation

### Added Logs

Standard library `logging` (`logging.getLogger(__name__)`) integrated across the 4 WebSocket session and transport modules:

- **ERR / ERROR**:
  - `pypost/core/qt/websocket_session.py` (`on_failed`): Logs unrecoverable session/handshake errors with category, message, and detail (`WebSocket session error occurred (category=%s, message=%s, detail=%s)`).
  - `pypost/core/qt/websocket_session.py` (`on_closed`): Logs when maximum reconnect attempts are exhausted (`WebSocket reconnection attempts exhausted (%d/%d)`).
- **WARNING**:
  - `pypost/core/qt/websocket_session.py` (`abort`): Logs immediate abort/termination events with current state (`Aborting WebSocket session immediately (current_state=%s)`).
  - `pypost/core/qt/websocket_session.py` (`on_tls_errors`): Logs TLS certificate verification failures, error count, and whether errors were bypassed (`WebSocket TLS certificate errors encountered (count=%d, ignored=%s): %s`).
  - `pypost/core/qt/websocket_session.py` (`_on_heartbeat_timeout`): Logs heartbeat timeout when peer fails to reply with pong (`WebSocket heartbeat timeout expired (no pong response within %.1fs)`).
  - `pypost/core/qt/websocket_transport.py` (`_on_error_occurred`): Logs low-level Qt socket errors (`QtWebSocket error occurred: category=%s, message=%s`).
  - `pypost/core/qt/websocket_transport.py` (`_on_ssl_errors`): Logs Qt SSL error events and ignore status (`QtWebSocket SSL errors encountered: count=%d, ignored=%s`).
- **INFO**:
  - `pypost/core/qt/websocket_session.py` (`open`): Logs connection initiation with target URL, TLS verification flag, heartbeat interval, and reconnect configuration.
  - `pypost/core/qt/websocket_session.py` (`on_opened`): Logs successful handshake establishment and negotiated subprotocol.
  - `pypost/core/qt/websocket_session.py` (`close`): Logs user or system close initiation with close code, reason, and active state.
  - `pypost/core/qt/websocket_session.py` (`on_closed`): Logs socket closure with code, reason, initiator (`peer` vs local), and state.
  - `pypost/core/qt/websocket_session.py` (`on_closed` reconnect branch): Logs scheduling of reconnection attempts with attempt count and delay.
  - `pypost/core/qt/websocket_session.py` (`_on_reconnect_timer`): Logs execution of scheduled reconnect attempts to target URL.
- **DEBUG**:
  - `pypost/core/qt/websocket_session.py` (`send_text`, `send_binary`): Logs outgoing frame transmission with byte size (raw message payloads and tokens are omitted).
  - `pypost/core/qt/websocket_session.py` (`on_text`, `on_binary`): Logs incoming frame reception with byte size (raw message payloads omitted).
  - `pypost/core/qt/websocket_session.py` (`on_pong`): Logs heartbeat pong latency in milliseconds and payload size.
  - `pypost/core/qt/websocket_session.py` (`_transition_to`): Logs state transitions (`Idle -> Connecting`, `Connecting -> Open`, etc.) and transition details.
  - `pypost/core/qt/websocket_session.py` (`_start_heartbeat`, `_on_heartbeat_interval`): Logs heartbeat timer setup and ping trigger events.
  - `pypost/core/qt/websocket_transport.py` (`open`, `send_text`, `send_binary`, `ping`, `close`, `abort`): Logs low-level Qt transport operations and frame byte sizes.
  - `pypost/core/websocket_session_policy.py` (`can_transition`, `calculate_backoff_delay`, `should_reconnect`): Logs transition validation results, backoff calculations with jitter, and reconnect policy evaluations.

### Log Structure

Log format used:
- **Structured logs**: Yes (parameterized format strings with discrete fields: `category`, `message`, `code`, `reason`, `peer`, `state`, `delay`, `bytes`).
- **Includes context**: Yes (session state, close codes, error categories, target URLs, latency measurements).
- **Log levels**: `DEBUG`, `INFO`, `WARNING`, `ERROR`.
- **Payload Privacy & Security**: Raw message contents, auth headers, and tokens are never logged; only metadata and byte sizes are recorded (`len(payload)`).

## External Signal Observability

`WebSocketSessionController` provides external observability via Qt signals:
- `state_changed = Signal(str, object)`: Emits state name and `StateDetail` on every lifecycle transition.
- `lifecycle_event = Signal(str, str)`: Emits high-level events (`opened`, `pong`, `closed`).
- `frame_received = Signal(object)`: Emits unmasked `RawFrame` for downstream stream observers.
- `frame_sent = Signal(object)`: Emits unmasked `RawFrame` for transmission tracking.
- `reconnect_scheduled = Signal(int, int, int)`: Emits `(attempt, max_attempts, delay_ms)`.
- `subprotocol_negotiated = Signal(str)`: Emits negotiated subprotocol string.
- `session_failed = Signal(str, str)`: Emits error category and user-facing error message.
- `tls_errors_raised = Signal(object)`: Emits certificate error tuple.

## Metrics Implementation

### Performance Metrics

- **Ping / Pong Latency**: Measured in milliseconds and emitted via `on_pong` (`lifecycle_event("pong", f"{elapsed_ms}ms latency")`) and logged at `DEBUG`.
- **Frame Throughput & Size**: Measured via `RawFrame.byte_size` on incoming and outgoing frames.
- **Reconnection Backoff Delay**: Exponential backoff duration in milliseconds computed and emitted via `reconnect_scheduled(attempt, max, delay_ms)`.

### System Health & Component Status

- **Session State**: Monitored through `SessionState` (`IDLE`, `CONNECTING`, `OPEN`, `CLOSING`, `CLOSED`, `RECONNECTING`, `FAILED`).
- **Heartbeat Health**: Active timer detection triggers `heartbeat_timeout` transition to `FAILED` if peer drops without TCP FIN.

## Monitoring Integration

- [x] Standard library `logging` integrated across all core engine and transport modules
- [x] Qt Signal event bus for UI and headless monitoring subscribers
- [x] Automated test coverage verifying logging formatting and payload sanitization (`test_websocket_structured_logging`)

## Validation Results

- [x] Logs are correctly formatted
- [x] Metrics / latency indicators are collected correctly
- [x] Logging works in error scenarios (DNS failure, heartbeat timeout, TLS cert rejection, reconnect exhaustion)
- [x] Large data structures and sensitive raw tokens are not logged
- [x] Flake8 is clean across all modules (`flake8 --jobs=1 pypost/`)
- [x] All automated tests pass (18/18 tests in websocket test suites)

## Notes

All logging hooks adhere strictly to architectural constraints:
- `pypost/core/websocket_transport_protocol.py` remains a pure interface/model module.
- `pypost/core/websocket_session_policy.py` remains Qt-free and uses standard library logging.
- `pypost/core/qt/websocket_transport.py` is the sole module importing `PySide6.QtWebSockets`.
- `pypost/core/qt/websocket_session.py` provides complete signal-based and log-based observability while remaining decoupled from UI widgets and masking policies.
