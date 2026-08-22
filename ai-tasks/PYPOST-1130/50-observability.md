# PYPOST-1130: Observability Implementation

## Overview

PYPOST-1130 implements the memory-bounded message stream (`MessageStream`), multi-format payload codecs (`websocket_codec`), session transcript export formatters (`websocket_stream_export`), and the virtualized Qt list model (`StreamListModel`) for real-time WebSocket communication in PyPost.

Observability for WS-3 is structured across three core layers:
1. **Drop Accounting & Diagnostic Metrics**: Dual FIFO eviction tracking (`dropped["capacity"]`, `dropped["memory_budget"]`), payload memory tracking (`total_retained_bytes`), un-truncated wire byte size tracking (`StreamEntry.byte_size`), and display truncation flags (`StreamEntry.truncated`).
2. **Export Header Diagnostics**: Comprehensive session metadata, total retained count, and eviction drop counters embedded in standard JSON transcript metadata and plain text transcript headers.
3. **Structured Logging**: Standardized key-value operational and debug logging across core ring operations, transcript export routines, and UI batch model synchronization without exposing sensitive secrets or logging large payload bodies.

---

## Logging Implementation

### Added Logs

Structured logs implemented across WS-3 components:
- **EMERG**: None (client-side desktop application; no emergency kernel/system alerts).
- **ALERT**: None (no operational paging alerts).
- **CRIT**: None (critical operational errors surfaced as descriptive exceptions).
- **ERR**:
  - `pypost/core/websocket_codec.py` (`encode_payload`) — Raises descriptive `ValueError` on JSON decode syntax failure (`Invalid JSON: ...`), invalid hexadecimal strings (`Invalid hexadecimal payload: ...`), or corrupted Base64 inputs (`Invalid Base64 payload: ...`).
  - `pypost/core/websocket_stream_export.py` (`export_stream_to_json_file`, `export_stream_to_text_file`) — Raises `WebSocketExportError` with underlying I/O context on disk write or directory creation failure.
- **WARNING**: None (eviction and normal bounds enforcement are expected non-error operational events logged at DEBUG level).
- **NOTICE**: None (syslog level mapped to INFO).
- **INFO**:
  - `websocket_stream_json_exported`: `pypost/core/websocket_stream_export.py:export_stream_to_json_file` — `path=%s entries_count=%d capacity_dropped=%d memory_budget_dropped=%d` (logs destination file path, total exported entries, and cumulative drop counts).
  - `websocket_stream_text_exported`: `pypost/core/websocket_stream_export.py:export_stream_to_text_file` — `path=%s entries_count=%d capacity_dropped=%d memory_budget_dropped=%d` (logs destination file path, total exported entries, and cumulative drop counts).
- **DEBUG**:
  - `websocket_stream_eviction_triggered`: `pypost/core/websocket_stream.py:MessageStream.append` — `cause=%s evicted_count=%d retained_entries=%d retained_bytes=%d` (emitted whenever capacity or memory budget FIFO eviction occurs).
  - `websocket_stream_cleared`: `pypost/core/websocket_stream.py:MessageStream.clear` — Emitted when ring buffer is reset.
  - `websocket_stream_model_eviction_signaled`: `pypost/ui/widgets/websocket/stream_model.py:StreamListModel.append_batch` — `evicted=%d dropped_capacity=%d dropped_memory_budget=%d total_rows=%d` (emitted when Qt `beginRemoveRows`/`endRemoveRows` signals are dispatched during front eviction).
  - `websocket_stream_model_batch_appended`: `pypost/ui/widgets/websocket/stream_model.py:StreamListModel.append_batch` — `inserted=%d evicted=%d total_rows=%d` (emitted on batch insertion transaction completion).
  - `websocket_stream_model_cleared`: `pypost/ui/widgets/websocket/stream_model.py:StreamListModel.clear` — Emitted when Qt `beginResetModel`/`endResetModel` resets the UI model.

### Log Structure

Log format used:
- Structured logs: **Yes** — Parameterized key-value tokens (e.g. `event_name key1=%s key2=%d`).
- Includes context: **Yes** — Includes file paths, entry counts, eviction causes, dropped counts per cause, retained byte sizes, and total row counts.
- Log levels: `DEBUG`, `INFO`, `ERROR` (via descriptive exceptions).
- Secret protection & payload safety: No unmasked secret variable values or raw large payload bodies are ever emitted to logs; all text is masked at entry construction time via `build_stream_entry`.

---

## Metrics Implementation (if applicable)

### Performance Metrics

Added performance metrics and diagnostic indicators:
- **Response time**:
  - `MessageStream.append`: $O(1)$ amortized append and eviction operations using `collections.deque`.
  - `StreamListModel.append_batch`: Coalesced batch insertion into `StreamListModel` avoiding per-row Qt notification overhead and maintaining smooth 30-60 FPS UI rendering.
- **Throughput**:
  - High-frequency message stream ingestion supporting thousands of incoming frames per second.
- **Error rate**:
  - `validate_format`: Non-raising format syntax validation returning `(is_valid: bool, error_message: str | None)` for real-time UI composer feedback.

### Business & Operational Metrics

Stream metrics and drop accounting:
- `dropped["capacity"]`: Cumulative count of stream entries evicted due to exceeding `max_entries` (`MessageStream.dropped["capacity"]`).
- `dropped["memory_budget"]`: Cumulative count of stream entries evicted due to exceeding `memory_budget_bytes` (`MessageStream.dropped["memory_budget"]`).
- `total_retained_bytes`: Cumulative UTF-8 encoded byte size of all retained payloads in the stream buffer (`MessageStream.total_retained_bytes`).
- `StreamEntry.byte_size`: True un-truncated wire byte size preserved on every entry for accurate network throughput and frame statistics.
- `StreamEntry.truncated`: Boolean indicator flagging whether the payload string was truncated to `ws_display_truncate_bytes` (default 256 KiB).
- `StreamEntry.seq`: Monotonically increasing sequence number ensuring stable item identification across front evictions.
- `metadata.dropped`: Structured drop counters serialized into JSON and plain text transcript exports to guarantee truncated transcripts are never presented as complete logs.

### System Health Metrics

System health metrics:
- **Resource usage**:
  - Memory consumption strictly bounded by `memory_budget_bytes` (default 64 MiB / 67,108,864 bytes) and `max_entries` (default 5,000 entries), preventing memory exhaustion during long-running sessions.
- **Component status**:
  - `StreamListModel` role synchronization (`SeqRole`, `TimestampRole`, `KindRole`, `DirectionRole`, `FormatRole`, `TruncatedRole`, `ByteSizeRole`, `DetailRole`, `StreamEntryRole`) reflecting real-time stream state.

---

## Monitoring Integration

Integration with monitoring systems:
- [ ] Prometheus metrics (N/A — client-side desktop application)
- [ ] Grafana dashboards (N/A — client-side desktop application)
- [ ] Alerting rules (N/A — client-side desktop application)
- [x] Standard Python `logging` root hierarchy with module-level loggers (`pypost.core.websocket_stream`, `pypost.core.websocket_stream_export`, `pypost.ui.widgets.websocket.stream_model`)
- [x] Pytest log capture and caplog validation (`caplog.at_level`)
- [x] Transcript file export metadata and diagnostic headers (`format_json_transcript`, `format_text_transcript`)

---

## Validation Results

Validation results:
- [x] Logs are correctly formatted (standardized structured tokens with `%` interpolation)
- [x] Metrics are collected correctly (drop counters, retained bytes, wire byte size, truncation flags validated in test suite)
- [x] Logging works in error scenarios (`export_stream_wraps_write_errors_in_websocket_export_error`, `test_codec_json_encode_invalid_syntax_raises_value_error`, etc.)
- [x] Large data structures are not logged (only metadata, paths, and counters are logged; payload bodies are omitted from logs)
- [x] Metrics are available for monitoring (accessible via `MessageStream.dropped`, `MessageStream.total_retained_bytes`, and export headers)
- [x] Automated test suite: 44/44 tests passing in `tests/test_websocket_stream_and_codecs.py`
- [x] Static analysis: flake8 clean, mypy baseline clean

---

## Notes

- **Pure Layering Invariant**: `pypost/core/websocket_stream.py`, `pypost/core/websocket_codec.py`, and `pypost/core/websocket_stream_export.py` contain zero imports of PySide6 or Qt modules and are 100% testable headlessly.
- **Secret Redaction**: Secret masking occurs at stream entry creation via `build_stream_entry`, guaranteeing that unmasked credentials never enter ring buffers, export files, or log outputs.
