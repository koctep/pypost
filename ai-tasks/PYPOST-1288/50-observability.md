# PYPOST-1288: Observability Implementation

## Logging Implementation

The WebSocket session controller now logs each transport handoff outcome. Accepted text and
binary messages produce `DEBUG` events named `websocket_send_accepted`; rejected or incomplete
handoffs produce `WARNING` events named `websocket_send_rejected`. The events contain message
kind and payload byte count. Rejection events also contain the session state. These are
structured key-value messages; they contain no payload, URL, connection identifier, or secret.

The existing send-attempt `DEBUG` messages and session lifecycle/error logs remain in place.
UI attempts blocked while the session is not open are observable through the existing
presenter warning; no successful-send event is emitted for them.

## Metrics Implementation

The presenter records `websocket_messages_total` with `direction="outbound"` and a `kind`
of `text` or `binary`, plus `websocket_message_bytes_total{direction="outbound"}` once per
accepted `frame_sent` signal. Text byte count is UTF-8 payload length; binary byte count is
raw payload length.
Blocked and rejected sends emit no `frame_sent` signal and do not change the counters. The
existing `MetricsTrackerProtocol` routes these counters to Prometheus or OpenTelemetry, so no
new instruments or labels are needed. Payload content and connection details are never metric
labels.

These counters provide outbound throughput and traffic volume. Existing WebSocket session
status and error metrics cover connection health; this task introduces no new latency or system
resource measurement because the accepted-send contract has no such requirement.

## Monitoring Integration

The counters are available through the existing Prometheus metrics endpoint and OpenTelemetry
tracker. The controller events use the existing Python logger, so configured log collection can
receive them. No dashboard or alerting change is required for this task. The developer metrics
catalog update belongs to Step 8.

## Validation Results

- The outbound metrics repro covers accepted text and binary payloads, UTF-8 byte lengths,
  blocked sends, and rejected handoffs.
- The same test checks accepted and rejected log events and verifies the accepted log output
  omits a non-ASCII payload.
- `make check PYTEST_ARGS='tests/test_websocket_outbound_metrics_repro.py
  tests/test_websocket_client_ui_repro.py tests/test_websocket_session_controller.py
  tests/test_websocket_session_engine_repro.py'` passed lint, all four affected test files,
  and AI task artifact verification.
- The first targeted `make test` run found only an expected test assertion typo: the session
  state string is `Open`, not `open`. The assertion was corrected before the passing gate.
