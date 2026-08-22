# PYPOST-1131: Observability Implementation

## Logging Implementation

### Added Logs

Structured production logging has been implemented across the WebSocket connection-security subsystem (`pypost/core/websocket_security_policy.py`, `pypost/core/qt/websocket_session.py`, `pypost/core/qt/websocket_transport.py`):

- **ERR**:
  - `pypost/core/qt/websocket_session.py`: `websocket_session_tls_validation_failed url=%s error=%s` - Logged when TLS certificate validation fails during handshake under strict policy, triggering transition to `SessionState.FAILED`.
  - `pypost/core/qt/websocket_session.py`: `websocket_session_failed category=%s message=%s detail=%s` - Logged when unrecoverable transport or protocol errors occur.
- **WARNING**:
  - `pypost/core/qt/websocket_session.py`: `websocket_ephemeral_tls_exception_granted session_state=%s` - Logged when an operator explicitly authorizes an ephemeral in-memory certificate validation bypass for testing.
  - `pypost/core/qt/websocket_session.py`: `websocket_tls_errors_encountered count=%d ignored=%s summary=%s` - Logged when certificate validation errors are emitted by the transport layer.
  - `pypost/core/qt/websocket_session.py`: `websocket_session_aborted current_state=%s` - Logged when immediate socket termination / abort is triggered.
  - `pypost/core/qt/websocket_transport.py`: `websocket_transport_ssl_errors_encountered count=%d errors=%s` - Logged by Qt transport adapter upon receiving `QWebSocket.sslErrors` with detailed error descriptions.
  - `pypost/core/qt/websocket_transport.py`: `websocket_transport_socket_error category=%s message=%s` - Logged when native socket errors occur.
- **INFO**:
  - `pypost/core/qt/websocket_session.py`: `websocket_ephemeral_tls_exception_revoked session_state=%s` - Logged when ephemeral TLS trust grant is revoked or purged on session termination.
  - `pypost/core/qt/websocket_session.py`: `Opening WebSocket session to %s (verify_tls=%s, security=%s, heartbeat=%.1fs, reconnect=%s, ephemeral_trust=%s)` - Logged on session open request with security classification and configuration.
  - `pypost/core/qt/websocket_session.py`: `WebSocket session opened successfully (subprotocol=%s)` - Logged on handshake completion.
  - `pypost/core/qt/websocket_session.py`: `Closing WebSocket session (code=%d, reason=%s, current_state=%s)` - Logged on clean close handshake initiation.
  - `pypost/core/qt/websocket_session.py`: `WebSocket connection closed (code=%d, reason=%s, peer=%s, state=%s)` - Logged on transport disconnection.
- **DEBUG**:
  - `pypost/core/websocket_security_policy.py`: `websocket_endpoint_security_classified url=%s verify_tls=%s classification=%s` - Logged when classifying URL scheme and host security.
  - `pypost/core/websocket_security_policy.py`: `websocket_host_loopback_evaluated host=%s is_loopback=%s` - Logged when evaluating host loopback interface status.
  - `pypost/core/websocket_security_policy.py`: `websocket_ephemeral_trust_decision_reset session_id=%s url=%s` - Logged when clearing in-memory ephemeral trust state.
  - `pypost/core/websocket_security_policy.py`: `websocket_tls_diagnostic_report_created url=%s error_count=%d` - Logged when building structured TLS diagnostic reports.
  - `pypost/core/qt/websocket_transport.py`: `websocket_transport_open_initiated url=%s max_bytes=%d subprotocols=%s verify_tls=%s` - Logged when starting low-level socket handshake.
  - `pypost/core/qt/websocket_session.py`: `WebSocket session state transition: %s -> %s (detail=%s)` - Logged on state machine transitions.
  - `pypost/core/qt/websocket_session.py`: Frame metadata events (byte sizes and directions; message content suppressed for security).

### Log Structure

Log format used:
- **Structured logs**: Yes (`<event_name> <key>=<value>` format and structured message prefixes)
- **Includes context**: Yes (session state, target URL, certificate error codes, verification modes, security classifications)
- **Log levels**: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- **Data privacy invariant**: Raw message payloads, authentication headers, tokens, and certificate keys are strictly excluded from log records; only frame byte sizes and public certificate subject/issuer strings are logged.

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics and diagnostic attributes:
- **Handshake latency & Pong latency**: Tracked via `on_pong(elapsed_ms)` in `pypost/core/qt/websocket_session.py` and surfaced in lifecycle signals.
- **Error rate**: Captured via `tls_errors_raised` and `session_failed` signals with discrete error categories (`"tls_error"`, `"socket_error"`, `"reconnect_exhausted"`).

### Business Metrics

Business / Security Posture Metrics:
- **Endpoint Security Classification**: Computed via `classify_endpoint_security()` and signaled via `security_classification_changed` (`"secure_tls"`, `"insecure_tls_exception"`, `"plaintext_remote"`, `"plaintext_loopback"`).
- **Ephemeral Trust Overrides**: In-memory count and state of active overrides via `EphemeralSessionTrustDecision`.

### System Health Metrics

System health metrics:
- **Session Lifecycle State**: Tracked in `WebSocketSessionController._state` (`SessionState.IDLE`, `CONNECTING`, `OPEN`, `CLOSING`, `CLOSED`, `RECONNECTING`, `FAILED`).
- **TLS Diagnostic Reports**: Structured metadata via `TlsDiagnosticReport` and `TlsCertificateError` (subject, issuer, fingerprint, expiry date).

## Monitoring Integration

Integration with monitoring systems:
- [x] Standard Python logging (`logging.getLogger("pypost.core.*")`) compatible with log aggregators (ELK, Loki, syslog)
- [x] Structured Qt Signals (`state_changed`, `security_classification_changed`, `tls_errors_raised`, `session_failed`) for UI presenter binding
- [x] Zero disk persistence invariant for temporary security bypasses

## Validation Results

Validation results:
- [x] Logs are correctly formatted with key-value pairs and structured prefixes
- [x] Security classifications are accurately evaluated and logged
- [x] Logging works in error scenarios (tested via `test_session_controller_tls_error_caplog_contract`)
- [x] Sensitive payloads and private tokens are not leaked into logs
- [x] Caplog test coverage in `tests/test_websocket_tls_policy.py` satisfies caplog contracts (C1/C5)

## Notes

All automated tests in `tests/test_websocket_tls_policy.py` (19 test cases) pass with 100% success.
Error-path testing uses pytest's `caplog` fixture to assert production `ERROR` and `WARNING` messages, preventing uncaptured live log spam while guaranteeing observability regression protection.
