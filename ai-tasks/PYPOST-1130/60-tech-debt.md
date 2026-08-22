# PYPOST-1130: Technical Debt Analysis

## Shortcuts Taken

1. **Static Binary Presentation Detection**:
   - `detect_binary_presentation(payload: bytes)` in `pypost/core/websocket_codec.py` statically returns `WsMessageFormat.HEX`. Content-aware heuristic sniffing (e.g. attempting UTF-8 decoding fallback, MsgPack envelope inspection, or Protobuf header recognition) was deferred to future payload inspection enhancements to keep the codec engine deterministic and lightweight.
2. **Re-encoding for Eviction Accounting**:
   - `MessageStream.append` and `StreamListModel.append_batch` calculate memory budget cost using `len(entry.payload.encode('utf-8'))` dynamically upon append and eviction rather than caching a calculated memory footprint on `StreamEntry`. While accurate for retained string memory, storing `payload_utf8_bytes` on `StreamEntry` could avoid repeated UTF-8 encoding during rapid eviction cycles.
3. **Substring Secret Masking**:
   - `_mask_secrets` in `pypost/core/websocket_stream.py` performs literal substring replacements sorted by value length (`text.replace(val, "***")`). It does not perform structural JSON value parsing or streaming token masking. While this strictly adheres to PyPost's existing secret masking standard (`pypost/core/sensitive_data_masking_policy.py`), large JSON frames with nested tokens could benefit from structured masking in the future.
4. **Simulation-Based Batch Eviction in UI Model**:
   - `StreamListModel._calculate_batch_evictions` copies `list(self._stream._entries)` into a temporary list and simulates FIFO eviction with `pop(0)` to determine precise row removal ranges before emitting Qt `beginRemoveRows`. For standard UI batch sizes (10–100 items), overhead is negligible, but an index calculation directly on `deque` without copying would be more optimal for large bulk insertions.

## Code Quality Issues

1. **Direct Protected Member Access across Architectural Boundary**:
   - `StreamListModel.append_batch` in `pypost/ui/widgets/websocket/stream_model.py` accesses protected attributes `self._stream._entries`, `self._stream._retained_bytes`, `self._stream._dropped_capacity`, and `self._stream._dropped_memory_budget` to synchronize Qt row removal/insertion signals with in-memory mutations.
   - *Refactoring opportunity*: Introduce an atomic batch-append method on `MessageStream` (e.g., `MessageStream.plan_batch_append(entries)` and `MessageStream.apply_batch(entries)`) that returns the exact eviction count and slice details, eliminating protected member coupling between the UI model and core data buffer while preserving Qt-free isolation.
2. **Code Point vs. Byte Slicing on Truncation**:
   - In `build_stream_entry`, display truncation uses string slicing (`sanitized[:truncate_bytes]`). For payloads containing multi-byte UTF-8 characters (e.g., emojis or CJK text), character slicing retains `truncate_bytes` characters rather than strict byte count. While this guarantees valid UTF-8 string boundaries and avoids broken multi-byte sequences, the in-memory string byte length may exceed `truncate_bytes` by a small factor.

## Missing Tests

1. **Ultra-High Throughput Burst Stress Tests**:
   - Existing unit tests cover batch insertions and dual eviction logic up to several hundred entries. Additional stress tests simulating sustained bursts (e.g. 50,000 frames/sec arriving from a high-speed background worker thread into the UI model buffer) can be added in integration test suites.
2. **QSortFilterProxyModel Integration Tests**:
   - `StreamListModel` provides the raw data source, but integration with `QSortFilterProxyModel` evaluating `StreamQuery` filtering dynamically in a live Qt view will be tested in WS-4 (`PYPOST-1131`).
3. **Read-Only / Disk Full Export Error Path Tests**:
   - `test_export_stream_wraps_write_errors_in_websocket_export_error` verifies invalid parent directory paths. Adding tests specifically covering filesystem permission denied (`EACCES`) and simulated disk full (`ENOSPC`) conditions across different OS platforms would further harden disk persistence testing.

## Performance Concerns

1. **Case-Insensitive Search Lowercasing**:
   - `StreamQuery.matches` calls `entry.payload.lower()` and `entry.detail.lower()` on every query evaluation. For maximum buffer capacity (5,000 entries) under rapid interactive typing in the search box, pre-caching lowercased representations or indexing text could prevent UI latency.
2. **Tuple Allocation in `MessageStream.snapshot()`**:
   - `MessageStream.snapshot()` allocates a new tuple of references on each invocation (`tuple(self._entries)`). While ideal for transcript exports and immutable snapshots, consumers should avoid polling `snapshot()` in tight animation or paint loops.
3. **Large String Rendering in Qt Item Views**:
   - `StreamListModel.data(..., DisplayRole)` returns full (truncated up to 256KB) payload strings. The downstream UI view delegate (in WS-4) must ensure viewport eliding / line clamping so Qt does not attempt to lay out 256KB of single-line text on every repaint.

## Follow-up Tasks

1. **PYPOST-1131 (WS-4: WebSocket UI Panels & Presenters)**:
   - Wire `StreamListModel` into `WebSocketMessageListView`, connect search filters and `StreamQuery` proxy models, implement auto-scroll lock toggles, and connect transcript export actions to file dialogs.
2. **PYPOST-1132 (WS-5: End-to-End WebSocket Testing & Echo Server Integration)**:
   - Build complete end-to-end test scenarios connecting `QtWebSocketTransport`, `WebSocketSessionController`, `MessageStream`, and `StreamListModel` against `WebSocketEchoServer` with live traffic.
3. **PYPOST-1141**: Refactor `MessageStream` to provide a public `calculate_batch_evictions(entries)` method and eliminate direct access to private members (`_entries`, `_retained_bytes`) from `StreamListModel` (2 SP).
4. **Pre-existing Test Failures Triage**:
   - No pre-existing test failures exist in the WebSocket domain. All 100/100 WebSocket tests (`test_websocket_*.py`) pass cleanly in 5.2s.
   - Full repository static analysis (`flake8`, `mypy`) passes with 0 errors across all modified and newly created modules.
