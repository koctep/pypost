# PYPOST-1137: Technical Debt Analysis

## Shortcuts Taken

- **Qt event loop pumping via polling loop**: In `pypost/core/websocket_mcp_tools.py` (`execute_websocket_probe`), the probe execution on `WebSocketProbeRunner` (a `QThread`) is awaited synchronously using a polling loop with `time.sleep(0.01)` and `QCoreApplication.processEvents()`. This avoided building an asynchronous `asyncio.Future` ↔ Qt signal bridge across thread boundaries, but introduces a 10ms polling interval.
- **Lightweight Connection stub for UI Contract Preview**: In `pypost/ui/widgets/websocket/connection_editor.py` (`_refresh_mcp_preview`), a transient `WebSocketConnection(name="preview", ...)` instance is constructed on the fly for preview generation rather than binding to the active connection model in the presenter.
- **Substring-only matching for stop conditions**: The `stop_when` stopping condition evaluator in `pypost/core/websocket_probe.py` uses simple substring containment (`stop_when in message`) rather than supporting JSONPath, regex, or structured field matching.

## Code Quality Issues

- **Probe runner responsibility cohesion**: `WebSocketProbeRunner` (`pypost/core/qt/websocket_probe_runner.py`) handles session slot concurrency acquisition/release, Qt event loop execution, transport instantiation, and deadline timeout management. Separating concurrency tokens and event loop management into dedicated helper primitives would improve modularity.
- **Transcript sanitizer env-map synthesis**: In `format_probe_transcript` (`pypost/core/websocket_probe.py`), secret strings in `hidden_keys` are injected into a synthetic environment map as both key and value to leverage `McpResponseSanitizer.sanitize_text`. While secure and effective, a direct set-based literal redaction method in `McpResponseSanitizer` would be cleaner.
- **MCPServerImpl protocol dispatch branching**: `MCPServerImpl` in `pypost/core/mcp_server_impl.py` handles HTTP request dispatch and WebSocket probe dispatch via `isinstance` checks. As additional protocols are added in the future, transitioning to a polymorphic `McpToolHandler` strategy registry will prevent file growth beyond the 325 LOC architectural limit.

## Missing Tests

- **Network-level socket reset / abrupt disconnection**: Test suite covers clean close, refuse, timeouts, and connection errors, but does not simulate mid-stream TCP RST or sudden peer connection drops during active frame ingestion.
- **High-concurrency MCP probe contention**: Stress tests simulating concurrent agent probes competing for the global `DEFAULT_MAX_CONCURRENT_MCP_CALLS` semaphore and `SessionSlots` pool.
- **Complex binary frame decoding**: Tests verify binary frame length logging, masking, and counting, but not specialized binary payload serialization or custom protocol codecs in probe responses.

## Performance Concerns

- **Polling latency floor**: The 10ms polling loop in `execute_websocket_probe()` introduces an artificial ~10ms latency floor for fast probes that complete within 1-2ms.
- **Unbounded transcript memory buffering for large message counts**: While `max_messages` is clamped to global ceilings (default 10), incoming large payloads are held in memory as `ProbeEvent` dataclasses before being sanitized and formatted.
- **Full-transcript sanitization overhead**: `McpResponseSanitizer.sanitize_text` evaluates multi-pass regex replacements across the concatenated event log string at the end of probe execution.

## Follow-up Tasks

- `NON-BLOCKER — pre-existing`: [PYPOST-1148](https://pypost.atlassian.net/browse/PYPOST-1148) — Fix `make check` full-suite pytest deadlock / socket teardown hanging when running full test suite concurrently.
- Refactor `execute_websocket_probe` to use an asynchronous Qt-to-asyncio signal bridge or `QThread.finished` callback to eliminate `QCoreApplication.processEvents()` sleep polling.
- Enhance `stop_when` parameter to support regex patterns and JSONPath expressions for structured WebSocket message streams.
- Extract tool registration and dispatch in `MCPServerImpl` into a modular `McpToolHandler` registry pattern to maintain long-term LOC limits.
