# PYPOST-1140: Observability Implementation

## Logging Implementation

### Added Logs

No new log events required. Existing DEBUG events (`ws_server_text_message_received`, `ws_server_binary_message_received`, `ws_server_text_message_sent`, `ws_server_binary_message_sent`) continue to report `total_received` / `total_sent` using live buffer lengths after truncation.

### Log Structure

- Structured logs: yes (existing `key=value` pattern)
- Includes context: `name`, `length`, `total_received` / `total_sent`
- Log levels: DEBUG only (test harness)

## Metrics Implementation

### Diagnostic properties

- **`max_history` property**: Read-only exposure of configured buffer cap (`None` = unbounded).
- **`_total_received_count`**: Internal cumulative receive counter used for `close_on_message_count` when buffers are truncated; not exposed as a public property (buffers remain the primary assertion surface).

Truncated buffer properties (`received_messages`, `sent_messages`, typed variants) reflect only the retained ring-buffer window when `max_history` is set.

## Monitoring Integration

- [ ] Prometheus metrics — N/A (test harness)
- [ ] Grafana dashboards — N/A
- [ ] Alerting rules — N/A
- [ ] Log aggregation — N/A

## Validation Results

- [x] Logs remain correctly formatted after truncation
- [x] `total_received` / `total_sent` in DEBUG logs match truncated buffer lengths
- [x] Large payloads are not logged (length only)
- [x] `close_on_message_count` still fires using `_total_received_count`

## Notes

Benchmark authors using `max_history` should expect DEBUG log counters to cap at the configured window, not total frames processed.
