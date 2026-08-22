# PYPOST-1130: WS-3 Bounded message stream, codecs and export

## Programming Language

Python is the implementation language for the application runtime, data structures, codecs, and automated test suites. English Markdown is used for workflow documentation and technical artifacts.

## Goals

PyPost is expanding to support real-time, bidirectional WebSocket communication (Epic PYPOST-1123). In high-throughput, streaming environments, an unbounded log of incoming and outgoing frames poses a critical risk of memory exhaustion, UI unresponsiveness, and data loss. Furthermore, real-time protocols exchange heterogeneous payloads (UTF-8 text, structured JSON, raw binary buffers, protocol buffers, audio/telemetry packets) that require bidirectional conversion, validation, and presentation formatting.

The goal of this task (WS-3) is to establish the memory-bounded stream storage, payload codecs, transcript export capabilities, and virtualized list model for WebSocket sessions:
- **Dual-dimension memory bounding:** Guarantee that a session's retained memory is strictly bounded by both maximum entry count and payload byte budget, with oldest-first eviction and transparent drop accounting.
- **Payload truncation with wire fidelity:** Retain large payloads truncated up to a configurable display limit for UI inspection while preserving and reporting true wire byte size.
- **Robust multi-format codecs:** Provide bidirectional encoding, decoding, and validation for Text, JSON, Hexadecimal, and Base64 formats, with automatic presentation detection for binary frames and persistent per-session format overrides.
- **Safe, reproducible transcript export:** Export complete or bounded session transcripts to standard JSON arrays and plain text files with consistent secret masking and drop metadata.
- **Virtualized UI model with stable identity:** Provide a `QAbstractListModel` implementation (`StreamListModel`) over the bounded ring with coalesced batch updates (`append_batch`) and stable row identity across front evictions.
- **Pure secret masking at stream entry creation:** Enforce that raw frames are converted into masked stream entries via a pure, Qt-free function (`build_stream_entry`) using explicit environment variables and hidden keys before entries reach memory buffers or export files.

## User Stories

- As an **API developer inspecting a WebSocket session**, I want incoming and outgoing messages decoded and formatted in readable representations (Text, JSON, Hexadecimal, Base64) with automatic presentation detection for binary frames, so that I can easily debug heterogeneous and binary protocol payloads.
- As an **API tester running high-volume or long-running WebSocket sessions**, I want PyPost's memory consumption to remain strictly capped through dual eviction (max entries and byte budget), with clear counters showing how many messages were dropped and why, so that the application never runs out of memory or degrades in performance.
- As a **developer testing services returning large payloads**, I want messages exceeding the display limit to be retained truncated for fast UI inspection while still reporting true wire byte size and being flagged as truncated, so that large payloads do not freeze the UI while preserving accurate network statistics.
- As a **team member sharing defect reproductions**, I want to export session transcripts to standard JSON array or plain text files containing full metadata, secret masking, and drop counters, so that I can attach clean, non-leaking evidence to issue reports.
- As a **UI engineer building WebSocket stream views (WS-4, WS-5)**, I want a `QAbstractListModel` over the ring buffer that accepts batched updates and maintains stable row identity across front eviction, so that list views render smoothly without flickering or excessive repaint overhead.
- As a **security engineer**, I want secret masking applied at the boundary where raw frames become stream entries using explicit environment variables and hidden keys, so that unmasked secrets are never stored in ring memory buffers or exported to disk.

## Definition of Done

This task is considered done when the following acceptance criteria are fully met and verified by automated tests:

1. **Dual Eviction & Drop Accounting**:
   - Appending entries when `max_entries` is exceeded evicts the oldest entry first and increments `dropped["capacity"]`.
   - Appending entries when `memory_budget_bytes` is exceeded evicts the oldest entries first and increments `dropped["memory_budget"]`.
   - Cumulative drop counts per cause are tracked accurately and exposed via `MessageStream.dropped`.
2. **Display Truncation & Wire Size Integrity**:
   - A payload whose byte size exceeds `ws_display_truncate_bytes` (default 256 KiB) is retained truncated up to the limit, flagged with `truncated=True`, and preserves its true wire size in `byte_size`.
3. **Codec Round Trips & Input Validation**:
   - Round-trip encoding and decoding hold for `text`, `json`, `hex`, and `base64` formats.
   - Invalid hexadecimal strings (e.g. non-hex characters, odd length) and invalid Base64 strings (e.g. invalid padding, corrupted characters) are rejected with specific, descriptive error messages.
   - Binary frame payload presentation defaults to hexadecimal format, and a user's format selection overrides the presentation for the duration of the session.
4. **Virtualized Stream List Model (`QAbstractListModel`)**:
   - `StreamListModel` exposes the stream ring buffer with stable row identity (`seq`) across front evictions.
   - The model emits standard `beginInsertRows`/`endInsertRows` and `beginRemoveRows`/`endRemoveRows` Qt signals.
   - `append_batch(entries)` is the sole entry point that mutates the underlying `MessageStream` from the UI path, performing insertions and eviction removals in a single transaction.
5. **Session Transcript Export**:
   - Exports session transcripts to JSON array format using `pypost.core.export_file_writer.write_json_export_file` and to Plain Text format (`ts direction size payload`).
   - Both export formats include drop counts (`capacity` and `memory_budget`) in metadata/headers so truncated transcripts are never presented as complete records.
   - Multiple export calls with identical inputs produce byte-identical output files.
6. **Pure Masking & Stream Entry Construction**:
   - `build_stream_entry(frame, *, env_vars, hidden_keys, truncate_bytes)` is a pure, Qt-free function in `pypost/core/websocket_stream.py`.
   - It replaces hidden variable values with `HIDDEN_PLACEHOLDER` using only the explicitly passed `env_vars` and `hidden_keys`, imports no `Environment` type, and is unit-tested without Qt.
   - A frame containing a hidden secret value never yields an unmasked `StreamEntry`.
7. **Stream Query Filtering**:
   - `StreamQuery` predicate evaluates direction (`in`, `out`, `all`), entry kind (`message`, `lifecycle`, `all`), payload format, search text, and lifecycle visibility, enabling Qt-free testing of filter logic.
8. **Strict Architectural Layering**:
   - `pypost/core/websocket_stream.py`, `pypost/core/websocket_codec.py`, and `pypost/core/websocket_stream_export.py` contain zero imports of `PySide6` or Qt modules and are 100% testable headlessly without a `QApplication`.
   - `pypost/ui/widgets/websocket/stream_model.py` is the only module in this story that imports PySide6.

## Task Description

### Problem Statement

During an active WebSocket connection, messages arrive continuously and asynchronously. In contrast to one-shot HTTP requests, a WebSocket session can exchange thousands of messages per second or remain open for hours. Without explicit bounds, storing all frames in memory leads to unbounded heap consumption, degraded garbage collection, UI freezing, and eventual out-of-memory crashes.

Furthermore:
- Raw WebSocket frames carry either UTF-8 text or arbitrary binary data. Developers need to inspect binary buffers as hex dumps or Base64 strings, format JSON payloads with syntax awareness, and validate outgoing messages before sending.
- Users need to export session transcripts to standard files for bug reports or auditing. Transcripts must include drop accounting (so users know if messages were lost due to buffer limits) and must never leak sensitive tokens or credentials.
- The UI layer requires a virtualized Qt list model (`QAbstractListModel`) to render high-throughput streams smoothly without creating per-row widget allocations or flickering during front-of-buffer evictions.

### Scope

**In Scope:**
- `pypost/core/websocket_stream.py`:
  - `StreamEntry` immutable dataclass representing a timestamped, masked stream event with sequence numbering, direction, wire size, display truncation flag, and payload format.
  - `MessageStream` bounded ring buffer with dual eviction (`max_entries`, `memory_budget_bytes`), drop accounting (`dropped["capacity"]`, `dropped["memory_budget"]`), snapshot extraction, and clearing.
  - `StreamQuery` predicate dataclass for filtering entries by direction, kind, format, text pattern, and lifecycle visibility.
  - `build_stream_entry(frame, *, env_vars, hidden_keys, truncate_bytes)` pure function converting a `RawFrame` into a masked, truncated `StreamEntry`.
- `pypost/core/websocket_codec.py`:
  - Encoders, decoders, and format validators for `text`, `json`, `hex`, and `base64`.
  - Automatic presentation detection for received binary payloads with default-to-hex and per-session override support.
- `pypost/core/websocket_stream_export.py`:
  - JSON array transcript formatter writing through `pypost.core.export_file_writer.write_json_export_file`.
  - Plain text transcript formatter (`ts direction size payload` lines).
  - Inclusion of drop count metadata in export headers/payloads.
- `pypost/ui/widgets/websocket/stream_model.py`:
  - `StreamListModel(QAbstractListModel)` virtualized model over `MessageStream`.
  - `append_batch(entries)` as the sole UI mutation entry point with proper `beginInsertRows`/`endInsertRows` and `beginRemoveRows`/`endRemoveRows` signaling.
- Unit and integration tests verifying dual eviction, drop counting, truncation, codecs, export formats, model signals, and secret masking.

**Out of Scope:**
- Stream view widgets, custom row delegates, search inputs, filter bars, and detail inspector panes (covered in WS-5).
- Composer UI widget, format selection dropdowns, preset panels, and sequence runners (covered in WS-6).
- Low-level network transport, socket adapters, and session lifecycle controllers (covered in WS-1).
- Saved connection profiles, collection persistence, and interchange (covered in WS-2).
- Dynamic variable propagation from environment presenters to UI tabs (covered in WS-4, WS-7).
- Model Context Protocol (MCP) probe runner (covered in WS-9).

### Constraints and Assumptions

- **Pure Layering Compliance:** Core modules (`websocket_stream.py`, `websocket_codec.py`, `websocket_stream_export.py`) must remain completely Qt-free and importable in headless/CLI environments.
- **Default Bounding Constants:**
  - Default `max_entries = 5000`.
  - Default `memory_budget_bytes = 64 MiB` (67,108,864 bytes).
  - Default `ws_display_truncate_bytes = 256 KiB` (262,144 bytes).
- **Sole UI Writer Invariant:** `StreamListModel.append_batch` must be the only code path that mutates the `MessageStream` on the UI thread, ensuring model signaling matches ring buffer mutations exactly.
- **Export Reusability:** JSON export must reuse `pypost.core.export_file_writer.write_json_export_file` for consistent directory creation and error wrapping.
- **Masking Isolation:** Masking must occur at entry construction time via `build_stream_entry`; no unmasked secrets may enter the ring buffer.

## Functional Requirements

- **FR-1: Bounded Ring Buffer & Dual Eviction**:
  - Store a chronological sequence of `StreamEntry` items in an append-only ring buffer (`MessageStream`).
  - Maintain a maximum entry capacity limit (`max_entries`, default 5,000). When appending an entry exceeds this capacity, evict the oldest entry and record an eviction under `"capacity"`.
  - Maintain a maximum retained payload memory budget (`memory_budget_bytes`, default 64 MiB). When appending an entry causes total retained payload byte size to exceed this budget, evict oldest entries until the budget is satisfied and record evictions under `"memory_budget"`.
  - Eviction must always proceed strictly oldest-first (FIFO).
- **FR-2: Drop Accounting & Observability**:
  - Track cumulative eviction counts in a mapping (`dropped`: `{"capacity": int, "memory_budget": int}`).
  - Expose drop counts so UI presenters and export formatters can accurately display how many messages were discarded and why.
  - Reset drop counts to zero when `clear()` is invoked on the stream.
- **FR-3: Display Truncation & Wire Size Tracking**:
  - Enforce `ws_display_truncate_bytes` (default 256 KiB) when creating stream entries.
  - If a frame payload exceeds the truncate limit, truncate the retained payload string to the limit, mark `truncated = True`, and preserve the true original payload length in `byte_size`.
  - If a frame payload is within the limit, retain the full payload string, mark `truncated = False`, and set `byte_size` to the payload's wire size.
- **FR-4: Multi-Format Payload Codecs**:
  - **Text (`text`)**: Encode Unicode strings to UTF-8 bytes; decode UTF-8 bytes to strings with replacement for invalid sequences.
  - **JSON (`json`)**: Validate JSON syntax; format/indent JSON strings; encode to UTF-8 bytes; decode JSON text.
  - **Hexadecimal (`hex`)**: Encode binary `bytes` to hexadecimal string representations; decode hexadecimal strings to binary `bytes`. Reject invalid hex strings (non-hex characters, odd length) with a descriptive error.
  - **Base64 (`base64`)**: Encode binary `bytes` to Base64 ASCII strings; decode Base64 strings to binary `bytes`. Reject corrupted Base64 strings with a descriptive error.
- **FR-5: Binary Presentation Detection & Persistence**:
  - Automatically detect incoming binary frame payloads and default their display presentation to hexadecimal (`hex`).
  - Allow the user or caller to explicitly override the presentation format (e.g. switch between `hex` and `base64`), persisting the preference for the active session.
- **FR-6: Pure Stream Entry Construction & Masking**:
  - Provide `build_stream_entry(frame: RawFrame, *, env_vars: Mapping[str, str], hidden_keys: Iterable[str], truncate_bytes: int) -> StreamEntry`.
  - Replace occurrences of hidden variable values with `HIDDEN_PLACEHOLDER` (`"***"`) in text payloads and lifecycle details.
  - Assign monotonically increasing sequence numbers (`seq`) starting from 1.
  - Record ISO-8601 UTC timestamp with millisecond precision (`ts_utc`).
  - Classify entry kind (`"message"` or `"lifecycle"`) and direction (`"in"`, `"out"`, or `"none"`).
  - Must not import or reference any `Environment` model type.
- **FR-7: Stream Query Predicate**:
  - Define `StreamQuery` with filter fields: `direction` (e.g. `IN`, `OUT`, `ALL`), `kind` (e.g. `MESSAGE`, `LIFECYCLE`, `ALL`), `payload_format` (optional `WsMessageFormat`), `search_text` (case-insensitive substring match on payload and detail), and `show_heartbeats` (boolean toggle for heartbeat lifecycle events).
  - Provide `MessageStream.matching(query: StreamQuery) -> Sequence[int]` returning sequence IDs of matching entries.
- **FR-8: Transcript Export**:
  - Provide JSON array export: serialize session entries as a formatted JSON array with root/header metadata including session timestamp, total entries, and drop counts (`capacity`, `memory_budget`).
  - Provide Plain Text export: format session entries into human-readable text lines with a header containing session summary and drop statistics, followed by lines in the format `[<ts_utc>] [<direction>] [<size>B] <payload>`.
  - Ensure exported payloads contain only masked values and reflect truncation flags.
  - Re-use `pypost.core.export_file_writer.write_json_export_file` for JSON export file writing.
- **FR-9: Virtualized Stream List Model (`StreamListModel`)**:
  - Implement `QAbstractListModel` wrapping `MessageStream`.
  - Support `append_batch(entries: Sequence[StreamEntry]) -> None`:
    - Calculate new row insertions and required front evictions.
    - Emit `beginRemoveRows` / `endRemoveRows` when eviction occurs.
    - Emit `beginInsertRows` / `endInsertRows` when new entries are added.
  - Provide model roles: `DisplayRole`, `UserRole` (returning `StreamEntry`), and custom roles for sequence ID, timestamp, direction, kind, and truncation flag.
  - Guarantee stable row identification via `seq` across front evictions.

## Non-Functional Requirements

- **NFR-1: Memory Bounds & Predictability**:
  - Retained payload memory in a single `MessageStream` must never exceed `memory_budget_bytes` (default 64 MiB), and entry count must never exceed `max_entries` (default 5,000), regardless of traffic volume.
  - O(1) amortized append and eviction operations using `collections.deque`.
- **NFR-2: UI Performance & High-Throughput Ingestion**:
  - `StreamListModel.append_batch` must batch multiple incoming entries into a single insert transaction, avoiding per-message UI overhead and enabling smooth 30-60 FPS UI rendering under high frame rates.
  - Front eviction must emit clean range removal signals (`beginRemoveRows(0, n-1)`) without recreating the model or invalidating unaffected rows.
- **NFR-3: Security & Secret Protection**:
  - Sensitive environment variables and hidden keys must be redacted before entries enter the ring buffer via `build_stream_entry`.
  - Export files and clipboard transcripts must never contain unmasked secret values.
- **NFR-4: Architectural Layering & Decoupling**:
  - `websocket_stream.py`, `websocket_codec.py`, and `websocket_stream_export.py` must contain zero Qt / PySide6 imports and depend only on the Python standard library.
  - `pypost/ui/widgets/websocket/stream_model.py` is the single Qt-aware bridge module and must not import private networking transport internals.
- **NFR-5: Testability & Quality Verification**:
  - All core stream, codec, and export modules must be 100% testable headlessly without `QApplication`.
  - `StreamListModel` must be verified using `QAbstractItemModelTester` or equivalent signal/index integrity tests under offscreen platform test runners.
  - Every test must enforce bounded execution with `@pytest.mark.timeout`.

## Main Entities and Attributes

- **StreamEntry (Immutable Dataclass)**:
  - `seq: int`: Monotonically increasing sequence number within the session (stable identity).
  - `ts_utc: str`: ISO-8601 UTC timestamp with millisecond precision (e.g. `2026-08-22T11:27:00.123Z`).
  - `kind: str`: Event kind (`"message"` or `"lifecycle"`).
  - `direction: str`: Transmission direction (`"in"`, `"out"`, or `"none"`).
  - `payload_format: str`: Payload format representation (`"text"`, `"json"`, `"hex"`, `"base64"`).
  - `payload: str`: Masked payload string, truncated to `ws_display_truncate_bytes` if over limit.
  - `byte_size: int`: True un-truncated wire byte size.
  - `truncated: bool`: Boolean flag indicating whether the payload was truncated.
  - `detail: str`: Supplementary text (e.g. close code, error message, lifecycle event reason).

- **MessageStream (Bounded Ring Buffer)**:
  - `max_entries: int`: Maximum number of entries retained (default 5,000).
  - `memory_budget_bytes: int`: Maximum cumulative payload bytes retained (default 64 MiB).
  - `append(entry: StreamEntry) -> tuple[int, str | None]`: Appends an entry, executes dual eviction, and returns count of evicted entries and eviction reason.
  - `snapshot() -> Sequence[StreamEntry]`: Returns an immutable snapshot of all currently retained entries.
  - `matching(query: StreamQuery) -> Sequence[int]`: Returns sequence numbers of entries satisfying the filter query.
  - `clear() -> None`: Empties the ring buffer and resets drop counters.
  - `dropped: Mapping[str, int]`: Returns dictionary of cumulative dropped entries (`"capacity"`, `"memory_budget"`).

- **StreamQuery (Filter Predicate)**:
  - `direction: Optional[str]`: Filter by direction (`"in"`, `"out"`, or `None` for all).
  - `kind: Optional[str]`: Filter by kind (`"message"`, `"lifecycle"`, or `None` for all).
  - `payload_format: Optional[str]`: Filter by format (`"text"`, `"json"`, `"hex"`, `"base64"`, or `None`).
  - `search_text: str`: Substring filter applied case-insensitively across payload and detail.
  - `show_heartbeats: bool`: Flag indicating whether heartbeat ping/pong lifecycle entries are included.

- **WebSocketCodec (Payload Encoding/Decoding Service)**:
  - `encode_payload(data: str, format: WsMessageFormat) -> bytes | str`: Converts user input string into wire format (str for text/json, bytes for hex/base64).
  - `decode_payload(payload: bytes | str, format: WsMessageFormat) -> str`: Converts wire frame payload into display string.
  - `detect_binary_presentation(payload: bytes) -> WsMessageFormat`: Determines default display format for binary frames (defaults to `hex`).
  - `validate_format(data: str, format: WsMessageFormat) -> tuple[bool, str | None]`: Validates text syntax for JSON, hex, or base64.

- **StreamExport (Transcript Export Engine)**:
  - `format_json_transcript(stream: MessageStream, metadata: Mapping[str, Any]) -> dict[str, Any]`: Formats session transcript as a structured JSON object.
  - `format_text_transcript(stream: MessageStream, metadata: Mapping[str, Any]) -> str`: Formats session transcript as human-readable plain text.
  - `export_stream_to_file(path: Path, stream: MessageStream, format: str, metadata: Mapping[str, Any]) -> None`: Writes exported transcript to disk using `export_file_writer`.

- **StreamListModel (Qt List Model Bridge)**:
  - `QAbstractListModel` subclass providing row count, index mapping, and custom role data access over `MessageStream`.
  - `append_batch(entries: Sequence[StreamEntry]) -> None`: Coordinates batch insertion and eviction removal transactions.

## User Scenarios

### Scenario 1: Stream Entry Intake, Masking, and Truncation
1. The WebSocket connection receives an incoming text frame containing JSON with a token matching a hidden environment variable (`{{ API_SECRET }}`).
2. `build_stream_entry` is called with the raw frame, `env_vars`, `hidden_keys`, and `truncate_bytes=262144`.
3. The function replaces the secret value with `***` and checks the payload size.
4. Because the payload size is below the truncation limit, `truncated` is set to `False` and `byte_size` reflects the wire byte length.
5. The resulting `StreamEntry` is returned ready for insertion into `MessageStream`.

### Scenario 2: Capacity Eviction Under High Message Count
1. A session configured with `max_entries=5000` already contains 5,000 entries.
2. A new `StreamEntry` arrives and is appended to `MessageStream`.
3. `MessageStream.append` detects that entry count would become 5,001.
4. The oldest entry (sequence 1) is evicted from the front of the deque.
5. `dropped["capacity"]` increments from 0 to 1.
6. The stream now contains entries with sequences 2 through 5,001.

### Scenario 3: Memory Budget Eviction Under Large Payloads
1. A session configured with `memory_budget_bytes=67108864` (64 MiB) receives large binary frames (e.g. 1 MiB each).
2. After 64 messages, total retained payload bytes reach 64 MiB.
3. Appending the 65th 1 MiB message causes total retained bytes to exceed 64 MiB.
4. `MessageStream.append` evicts the oldest retained entries until the total payload size is below 64 MiB.
5. `dropped["memory_budget"]` increments by the number of evicted entries.
6. `StreamListModel.append_batch` signals `beginRemoveRows` for the evicted range and `beginInsertRows` for the new entry.

### Scenario 4: Codec Round Trips Across Formats
1. An operator types a JSON payload into the composer: `{"action": "subscribe", "channel": "telemetry"}`.
2. `encode_payload(..., WsMessageFormat.JSON)` validates JSON syntax and produces UTF-8 encoded text for transmission.
3. An incoming binary message `b"\x01\x02\x03\x04"` is received.
4. `detect_binary_presentation` assigns `WsMessageFormat.HEX`.
5. `decode_payload(..., WsMessageFormat.HEX)` formats the payload as `"01020304"`.
6. The operator switches format to `BASE64`; `decode_payload(..., WsMessageFormat.BASE64)` displays `"AQIDBA=="`.

### Scenario 5: Rejection of Invalid Hex and Base64 Payloads
1. An operator attempts to send hexadecimal data containing invalid characters: `"0102ZZ"`.
2. `validate_format("0102ZZ", WsMessageFormat.HEX)` fails and returns `(False, "Invalid hexadecimal digits at position 4")`.
3. An operator attempts to send Base64 data with invalid length/padding: `"AQIDB"`.
4. `validate_format("AQIDB", WsMessageFormat.BASE64)` fails and returns `(False, "Incorrect padding for Base64 string")`.
5. The invalid payload is rejected before reaching the network transport.

### Scenario 6: Transcript Export with Drop Accounting
1. An operator opens a session that experienced 15 capacity evictions and 3 memory budget evictions.
2. The operator requests a JSON transcript export.
3. `format_json_transcript` generates a JSON payload containing:
   - `metadata`: `{"dropped": {"capacity": 15, "memory_budget": 3}, "total_retained": 5000}`.
   - `entries`: Array of 5,000 masked `StreamEntry` objects.
4. `export_stream_to_file` delegates file creation and writing to `pypost.core.export_file_writer.write_json_export_file`.
5. The exported file on disk accurately records the dropped message counts in its header so readers know the log is bounded.

## Q&A

| Question | Answer |
| --- | --- |
| Why is dual eviction (both max entries and byte budget) required? | An entry cap alone does not prevent memory exhaustion if a peer sends large messages (e.g. 5,000 entries of 1 MiB each = 5 GiB RAM). Conversely, a byte budget alone does not bound UI row count if a peer sends millions of 10-byte messages. Dual eviction guarantees that both RAM usage and UI virtual row count remain strictly bounded. |
| Why is `StreamListModel.append_batch` the sole ring writer on the UI path? | To avoid race conditions, model-view desynchronization, and UI stutter. By routing all stream insertions through `append_batch` on the UI thread, model insert and eviction remove signals are emitted atomically in sync with the underlying `MessageStream` mutations. |
| Why does `build_stream_entry` take explicit `env_vars` and `hidden_keys` rather than an `Environment` object? | To enforce strict architectural layering. `pypost/core/websocket_stream.py` remains a pure, Qt-free module that does not import domain environment models. Passing explicit dicts and iterables keeps the function pure, side-effect free, and easily unit-testable. |
| Why is JSON transcript export formatted as a JSON array rather than NDJSON (Newline Delimited JSON)? | Reusability and consistency. PyPost's shared export writer (`pypost.core.export_file_writer.write_json_export_file`) handles atomic writing, directory creation, and error wrapping for standard JSON structures, matching collection and environment exports (RFC PYPOST-1124 A-6.5). |
| How does `StreamListModel` maintain stable row identity when the oldest entries are evicted from the front? | Each `StreamEntry` is assigned a monotonic, immutable `seq` integer at creation. Front eviction increments the base index but does not alter the `seq` numbers of remaining entries. The detail pane and UI selections track entries by `seq` rather than transient row indices. |
| What happens when an incoming binary frame cannot be decoded as UTF-8? | Binary frames (`FrameType.BINARY` / `bytes`) are automatically routed to binary codecs. `detect_binary_presentation` defaults to hexadecimal (`hex`), rendering byte values as two-character hex pairs (`01020304`) with an option for Base64 (`AQIDBA==`). UTF-8 decode is not forced on raw binary frames. |
| How is secret masking verified to prevent credential leakage? | `build_stream_entry` applies `_redact_hidden_values` and `sanitize_text` to incoming and outgoing payloads before returning a `StreamEntry`. Automated unit tests assert that raw frames containing hidden values never produce unmasked stream entries, export records, or model data. |
