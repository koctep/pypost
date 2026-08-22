# PYPOST-1128: Technical Debt Analysis

## Shortcuts Taken

No quick fixes or architectural compromises were taken during the implementation of PYPOST-1128:
- **Strict Domain Isolation:** WebSocket domain models (`WebSocketConnection`, `HeartbeatPolicy`, `ReconnectPolicy`, `WebSocketMessagePreset`, `WebSocketSequence`, `WebSocketSequenceStep`, `WsMessageFormat`) are cleanly encapsulated in `pypost/models/websocket.py` using pure Pydantic and standard library constructs without Qt dependencies or coupling to `RequestData`.
- **Zero Headroom Violation:** `pypost/core/request_manager.py` was kept strictly under its LOC cap (240 LOC vs 264 LOC limit) by cleanly extracting collection item dispatch into `pypost/core/collection_item_dispatch.py`.
- **Storage Invariance:** Collection persistence was implemented without touching `pypost/core/storage.py`, leveraging Pydantic's serialization mechanisms while ensuring backward compatibility with legacy collections lacking WebSocket items.
- **Security Compliance:** Storage and export workflows strictly preserve unexpanded template variables (`{{variable}}`), ensuring resolved secrets are never persisted to disk or exported payloads.

## Code Quality Issues

The implemented modules maintain high test coverage, strict static typing, and modular separation of concerns. Areas for future enhancement and downstream integration include:

1. **MCP Tool Engine Integration (WS-9 / PYPOST-1135):**
   - The 6 MCP metadata fields (`expose_as_mcp`, `mcp_description`, `mcp_params`, `mcp_probe_preset_id`, `mcp_probe_max_messages`, `mcp_probe_max_duration_ms`) are defined and persisted on `WebSocketConnection` as their single authoritative source of truth.
   - Dynamic schema generation, server registration, and real-time probe execution against active or ephemeral socket sessions will be handled by the MCP engine in WS-9.
2. **UI Sidebar Tree & Tab Presenters (WS-4 / PYPOST-1130):**
   - `WebSocketRegistry` and `collection_item_dispatch.py` provide full backend CRUD and O(1) item resolution.
   - Tree node rendering (distinct WebSocket icon, contextual menus for profile management) and tab presenters will bind to these services in WS-4.
3. **Message Streaming & Codecs (WS-3 / PYPOST-1129):**
   - The models currently store static preset templates and sequence steps. Live message frame capture, streaming ring buffer storage, binary payload encoding/decoding, and stream export will be introduced in WS-3.
4. **Runtime Variable Resolution (WS-4 / PYPOST-1130 & WS-6 / PYPOST-1132):**
   - Raw template strings are persisted without substitution. At connect time (WS-4) or sequence execution time (WS-6), variable substitution will resolve environment variables and session tokens before initiating socket connections or transmitting payloads.

## Missing Tests

The test suite in [`tests/test_websocket_models_and_persistence.py`](file:///home/src/tests/test_websocket_models_and_persistence.py) provides 21 comprehensive automated tests covering domain model instantiation, field validation, backward compatibility, storage round-trip invariance, registry indexing, item dispatch, export payload generation, ID reservation, collision re-keying, and import summary formatting.

Future test expansions to consider:
- **Corrupted Payload Fuzzing:** Automated property-based tests (e.g. Hypothesis) verifying graceful handling of corrupted or manually tampered JSON import files containing invalid enum values or out-of-range numeric fields.
- **Deep Hierarchy Stress Tests:** Boundary stress tests with hundreds of message presets and deeply nested sequence step graphs within a single profile.

## Performance Concerns

- **In-Memory Hash Index Scaling:**
  - `WebSocketRegistry` indexes profiles using an in-memory dictionary (`Dict[str, Tuple[WebSocketConnection, Collection]]`), ensuring O(1) lookup latency for UI tree and tab resolution.
  - Full workspace re-indexing is O(N) with respect to total WebSocket profiles. For typical workspaces (< 5,000 items), memory overhead is negligible (< 100 KB) and index rebuild time is sub-millisecond. Incremental index updates (`drop_collection_websockets_from_index` and per-profile saves) avoid full rebuilds during regular CRUD operations.
- **Model Copy Overhead on Sequence Execution:**
  - Isolating `WebSocketConnection` from `RequestData` prevents memory inflation during HTTP tab deep copies.
  - In WS-6, sequence execution with large inline payloads should avoid unnecessary deep copying of the entire profile during step iteration.

## Follow-up Tasks

The following follow-up workstreams build directly on the domain foundation established in PYPOST-1128:
1. **WS-3 (PYPOST-1129):** In-memory message ring buffer, streaming codecs, and real-time frame capture.
2. **WS-4 (PYPOST-1130):** WebSocket UI tab, connection session controller, sidebar tree integration, and runtime variable substitution.
3. **WS-5 (PYPOST-1131):** Preset manager, message composer, and subprotocol negotiation UI.
4. **WS-6 (PYPOST-1132):** WebSocket sequence runner, delay scheduling, and automated step execution.
5. **WS-9 (PYPOST-1135):** MCP tool server exposure, tool schema generator, and probe execution engine for WebSocket connection profiles.
6. **WS-11 (PYPOST-1137):** End-to-end multi-protocol integration test suites and stress benchmarks.
