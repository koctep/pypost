# PYPOST-1135: Observability Implementation

## Logging Implementation

### Added Logs

The following structured log events are implemented and maintained across WebSocket components for environment templating and secret masking:

- **EMERG**: None (not applicable for client-side desktop session operations).
- **ALERT**: None (not applicable for client-side desktop session operations).
- **CRIT**: None (fatal crashes handled by top-level PySide/Python exception handlers).
- **ERR**: None (operational errors handled via `session_failed` and `WebSocketExportError` with WARNING level).
- **WARNING**:
  - `pypost/ui/presenters/websocket_presenter.py`: `websocket_send_blocked_not_open state=<state>` - logged when send is attempted while session is not open.
  - `pypost/ui/presenters/websocket_presenter.py`: `run_sequence_blocked_not_open state=<state>` - logged when sequence execution is attempted on a non-open session.
  - `pypost/ui/presenters/websocket_presenter.py`: `run_sequence_not_found seq_id=<seq_id>` - logged when a requested sequence identifier is missing.
  - `pypost/core/websocket_stream_export.py`: `websocket_stream_export_file_failed format=<format> error=<exc>` - logged when transcript disk write fails.
- **NOTICE**: None (Python standard `logging` levels used).
- **INFO**:
  - `pypost/ui/presenters/websocket_presenter.py`: `websocket_connect_initiated url=<masked_url>` - logged when initiating connection; the target URL is strictly passed through `sanitize_text` with active environment variables and hidden keys to ensure sensitive query parameters or tokens are redacted before logging.
  - `pypost/ui/presenters/websocket_presenter.py`: `websocket_disconnect_initiated` - logged on user or automated disconnect request.
  - `pypost/ui/presenters/websocket_presenter.py`: `websocket_presenter_teardown` - logged during presenter and session teardown.
  - `pypost/core/websocket_stream_export.py`: `websocket_stream_export_file_completed format=<format> entries_count=<count> path=<path>` - logged upon successful stream export to disk.
- **DEBUG**:
  - `pypost/ui/presenters/websocket_presenter.py`: `websocket_sending_message length=<length>` - logs the length of outgoing message payload, strictly omitting raw payload text to guarantee zero credential leakage.
  - `pypost/core/websocket_stream.py`: `websocket_stream_on_mask_applied_failed error=<exc>` - logged if metric callback fails.
  - `pypost/core/websocket_stream.py`: `websocket_stream_eviction_triggered cause=<cause> evicted_count=<count> retained_entries=<retained> retained_bytes=<bytes>` - logged when dual FIFO buffer evicts old frames.
  - `pypost/core/websocket_stream.py`: `websocket_stream_cleared` - logged when stream buffer is cleared.
  - `pypost/ui/widgets/websocket/stream_model.py`: `stream_model_batch_appended added=<added> new_total=<total> evicted=<evicted>` - logged during virtualized UI model batch updates.
  - `pypost/ui/widgets/websocket/stream_model.py`: `stream_model_cleared` - logged when UI stream model is cleared.

### Log Structure

- Structured logs: **Yes** (`snake_case_event key=value ...` formatting following `doc/dev/logging.md`).
- Includes context: **Yes** (includes `url` [masked], `state`, `length`, `format`, `entries_count`, `path`, `cause`, `evicted_count`).
- Log levels: `INFO`, `WARNING`, `DEBUG`.
- **Zero Secret Leakage Invariant:** Message payloads (inbound and outbound), handshake header values, and unmasked query parameters are strictly excluded from all log records across all log levels. Verified by automated test `test_zero_secret_leakage_in_presenter_and_export_logging`.

## Metrics Implementation

### Performance Metrics

- **Response time**: Not applicable to PYPOST-1135 (WebSocket probe latency metrics are owned by WS-9 / WS-10).
- **Throughput**: WebSocket message and byte throughput metrics (`websocket_messages_total`, `websocket_message_bytes_total`) are owned by WS-10.
- **Error rate**: WebSocket session error and drop metrics are owned by WS-10.

### Business Metrics

- Not applicable for desktop client environment resolution and secret masking.

### System Health Metrics

- **Security & Masking Metrics**:
  - `hidden_value_masks_applied_total`: Prometheus / OpenTelemetry counter tracking total secret masking occurrences.
    - **Surface Label**: `surface="websocket"` (extends existing counter in `pypost/core/metrics_registry.py:161` and `pypost/core/metrics_otel.py:174`).
    - **Trigger**: Incremented each time a hidden environment variable value is detected and masked during stream ingestion (`build_stream_entry` for sent messages, received frames, and lifecycle events) or egress processing.
    - **Integration**: `build_stream_entry` triggers `on_mask_applied` callback which invokes `WebSocketPresenter._on_mask_applied()`, incrementing `metrics.hidden_value_masks_applied.labels(surface="websocket")` / `metrics.track_hidden_value_mask_applied(surface="websocket")`.
    - **Zero Leakage**: Metric labels contain only low-cardinality metadata (`surface="websocket"`); sensitive variable names and secret values are never included in metric labels or samples.

## Monitoring Integration

- [x] Prometheus metrics: `hidden_value_masks_applied_total{surface="websocket"}` registered in `MetricsRegistry`.
- [x] OpenTelemetry metrics: `hidden_value_masks_applied_total` registered in `MetricsOTel`.
- [ ] Grafana dashboards: (Out of scope for this story; centralized dashboards configured separately).
- [ ] Alerting rules: (Out of scope for this story).
- [x] Log aggregation (ELK, Loki, etc.): Standard structured log output compatible with log collectors.

## Validation Results

- [x] Logs are correctly formatted (`snake_case_event key=value`).
- [x] Metrics are collected correctly (`hidden_value_masks_applied_total{surface="websocket"}` tested in `test_hidden_value_masks_applied_metric_incremented_on_masking` and `test_presenter_increments_metric_when_masking_frames`).
- [x] Logging works in error and edge-case scenarios (`websocket_send_blocked_not_open`, `run_sequence_blocked_not_open`, `websocket_stream_export_file_failed`).
- [x] Large data structures and message payloads are not logged (only length and low-cardinality attributes are emitted).
- [x] Secret tokens, hidden environment values, and sensitive query parameters never leak into logs or metric labels (`test_zero_secret_leakage_in_presenter_and_export_logging`).
- [x] Metrics are available for monitoring via `MetricsRegistry` and `MetricsOTel`.

## Notes

- Stream ingestion masking (Tier 1) applies exact replacement for hidden environment variables in `build_stream_entry` so live stream debugging preserves non-secret structure without destructive heuristic alteration.
- Egress masking (Tier 2) applies full heuristic regex sanitization (`sanitize_text`) to clipboard copies and file exports.
- Handshake resolution occurs strictly once at connect time; mid-session environment modifications do not trigger mid-session log or connection mutation.
- Outbound payload resolution evaluates templates dynamically per-send, ensuring dynamic variables can be sent while maintaining zero secret leakage in logs.
- STEP 6 is marked `[/]` in `00-roadmap.md` pending independent verification by the acceptance gate.
