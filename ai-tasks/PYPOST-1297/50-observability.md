# PYPOST-1297: Observability Implementation

## Summary

No production logging or metrics change is needed. This task changes only test code
(`tests/test_websocket_outbound_metrics_repro.py`). `git diff --stat -- pypost` is empty.

The outbound WebSocket metrics already exist; PYPOST-1288 added them. This task adds
end-to-end coverage for them through a real Qt loopback send. The task makes the existing
observability more trustworthy and adds no new signals.

## Logging Implementation

### Added Logs

None. The send path already has the log events listed below. No new log lines are needed to
diagnose the scenarios this task covers.

- **EMERG / ALERT / CRIT / ERR / NOTICE / INFO**: N/A — no runtime code changed.
- **WARNING**: N/A (no new log lines added). Existing logs are listed below.
- **DEBUG**: N/A (no new log lines added). Existing logs are listed below.

### Existing Log Events on the Outbound Send Path

These were checked in code at base `286b3a4c`.

| Level | Event | Location | Diagnoses |
| --- | --- | --- | --- |
| WARNING | `websocket_send_rejected kind=<text\|binary> bytes=%d state=%s` | `pypost/core/qt/websocket_session.py` `send_text` / `send_binary` | Transport refused the send. No `frame_sent` is emitted, so no metric is incremented. |
| DEBUG | `websocket_send_accepted kind=<text\|binary> bytes=%d` | `pypost/core/qt/websocket_session.py` `send_text` / `send_binary` | Transport accepted the send. `frame_sent` follows, which increments the metrics. |
| DEBUG | `Sending WebSocket text/binary frame (%d bytes)` | `pypost/core/qt/websocket_session.py` | Send attempt with its UTF-8 or raw size |
| DEBUG | `QtWebSocketTransport sending text/binary frame (%d bytes)` | `pypost/core/qt/websocket_transport.py` | Reached the Qt socket. The transport returns `False` if the socket is not connected or the byte count Qt reports does not match. |
| WARNING | `websocket_send_blocked_not_open state=%s` | `pypost/ui/presenters/websocket_presenter.py` `handle_send_message` | Composer send attempted while the session is not `OPEN` |

The event names `websocket_send_rejected` and `websocket_send_accepted` are already checked
with caplog by the PYPOST-1288 fake-transport tests in the same file.

### Log Structure

- Structured logs: yes (`event_name key=value` format)
- Includes context: yes (kind, byte size, session state). Payload content is not logged.
- Log levels: WARNING, DEBUG (send path)

## Metrics Implementation

### Metrics Covered by the New Real-Loopback Test

`_on_frame_sent` in `pypost/ui/presenters/websocket_presenter.py` records these metrics.
They are registered in `pypost/core/metrics_registry.py` (Prometheus) and in
`pypost/core/metrics_otel.py`. Names, labels, and the catalog are unchanged.

| Metric | Type | Labels | Change per accepted send |
| --- | --- | --- | --- |
| `websocket_messages_total` | Counter | `direction="outbound"`, `kind="text"\|"binary"` (`FrameType` value) | +1 on the series for the frame's kind. The other kind does not change. |
| `websocket_message_bytes_total` | Counter | `direction="outbound"` | + payload byte size: UTF-8 length for text, raw length for binary |

Test `test_real_loopback_send_records_outbound_metrics_and_reaches_peer` checks these
before/after deltas with `get_sample_value` on an isolated `MetricsRegistry`:

| Row | Send | `messages_total` delta | `bytes_total` delta |
| --- | --- | --- | --- |
| 0 | non-ASCII text (11 chars, 18 UTF-8 bytes) | text +1, binary +0 | +18 |
| 1 | binary (6 bytes) | text +0, binary +1 | +6 |
| 2 | empty text | text +1, binary +0 | +0 |
| 3 | empty binary | text +0, binary +1 | +0 |

A rejected send records no metric. The PYPOST-1288 fake-transport tests already cover this.

### Performance / Business / System Health Metrics

N/A. No runtime behaviour changed, so no new performance, business, or health signal is
needed.

## Diagnostic Surface of the Test

If the metric wiring regresses, the test's failure messages point to the faulty row and
signal:

- `row N <kind> (<size> bytes) count delta: expected text=+X binary=+Y, got text=+A binary=+B`.
  Wrong or missing kind label, a double count, or `frame_sent` not emitted.
- `row N <kind> (<size> bytes) bytes delta: expected +S, got +B`. Character count used
  instead of UTF-8 byte count, or a wrong size.
- `row N <kind> (<size> bytes) not received by peer`. The bounded `wait_until` (5 s) timed
  out. The metrics were recorded, but the message did not reach the peer.
- `row N ... peer kind mismatch` / `peer payload mismatch`. Text/binary mixed up, or payload
  corrupted on the wire.
- Final `server.received_*_messages` list equality. Extra or missing messages at the peer.

The Step 3 mutation probe (M1-M4, `30-failing-repro.md`) showed that each regression
fails with its designed first assertion line.

## Monitoring Integration

- [x] Prometheus metrics — existing, unchanged (`metrics_registry.py`)
- [ ] Grafana dashboards — N/A, out of scope
- [ ] Alerting rules — N/A, out of scope
- [ ] Log aggregation — N/A, no new logs

## Validation Results

- [x] Logs are correctly formatted. Existing event names checked in code. No new logs.
- [x] Metrics are collected correctly. Checked end-to-end by the new real-loopback test.
- [x] Logging works in error scenarios. `websocket_send_rejected` is covered by PYPOST-1288
  tests.
- [x] Large data structures are not logged. Only kind, size, and state are logged, never the
  payload.
- [x] Metrics are available for monitoring. The registry and catalog are unchanged.

## Notes

This step is N/A for production code. The task is coverage-only, and the observability it
targets (PYPOST-1288 outbound metrics) was already in place. No logging or metrics were added.
