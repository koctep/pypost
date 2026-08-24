# PYPOST-1141: Observability Implementation

## Logging Implementation

### Added Logs

No new log events were added. This task is an internal API refactor that preserves existing observability.

### Existing Logs Preserved

- `websocket_stream_eviction_triggered`: `pypost/core/websocket_stream.py:MessageStream.append` — unchanged; single-entry path only.
- `websocket_stream_model_eviction_signaled`: `pypost/ui/widgets/websocket/stream_model.py:StreamListModel.append_batch` — preserved with same key-value fields (`evicted`, `dropped_capacity`, `dropped_memory_budget`, `total_rows`).
- `websocket_stream_model_batch_appended`: `pypost/ui/widgets/websocket/stream_model.py:StreamListModel.append_batch` — preserved (`inserted`, `evicted`, `total_rows`).

### Log Structure

- **Structured logs**: Yes (existing DEBUG key-value format).
- **Includes context**: Eviction counts and row totals; no payload bodies logged.
- **Log levels**: DEBUG only for batch eviction signaling.

## Metrics Implementation

### Performance Metrics

No new Prometheus or OTel metrics. Batch eviction remains a UI-thread hot path; existing stream drop counters (`MessageStream.dropped`) continue to aggregate capacity and memory-budget evictions.

### Business Metrics

- `websocket_stream_entries_dropped_total{reason}` (WS-10): Unaffected; drop counters updated via `apply_batch_evictions` identically to pre-refactor.

## Observability Notes

- Eviction planning (`calculate_batch_evictions`) is intentionally silent — it is a pure simulation with no side effects.
- If future profiling shows batch planning overhead, consider DEBUG-level timing on `calculate_batch_evictions` only (not added in this 1 SP task).
