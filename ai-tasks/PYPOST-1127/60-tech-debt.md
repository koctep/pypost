# PYPOST-1127: Technical Debt Analysis

## Shortcuts Taken

Minimal to no shortcuts were taken in the implementation of the core WebSocket session engine and transport quarantine:
- **Clean Layered Architecture**: Adhered strictly to the 4-module isolation boundary (`websocket_transport_protocol.py`, `websocket_session_policy.py`, `qt/websocket_transport.py`, `qt/websocket_session.py`).
- **Qt Isolation**: `PySide6.QtWebSockets` is strictly quarantined in `pypost/core/qt/websocket_transport.py`. Pure policy and protocol definitions remain completely Qt-free.
- **Synchronous Event Bridging**: Qt socket signals in `QtWebSocketTransport` directly invoke synchronous listener callbacks on `WebSocketTransportListener`. For high-throughput scenarios, intermediate decoupling queues are deferred to the downstream ring buffer layer (WS-3).
- **Default Factory Binding**: `WebSocketSessionController` defaults its transport factory to `QtWebSocketTransport(parent=self)`, with full dependency injection support via `set_transport_factory()`.

## Code Quality Issues

1. **Downstream Coupling & Data Flow (WS-2, WS-3, WS-4)**:
   - `RawFrame` Memory Ownership: `RawFrame` holds payload as an in-memory `str` or `bytes` object. For high-volume streaming sessions, unmanaged retention of these frames by downstream consumers could lead to memory pressure. Downstream circular ring buffering (WS-3 / PYPOST-1129) and SQLite persistence (WS-2 / PYPOST-1128) must ingest and manage frame lifecycles.
   - Masking Separation: `WebSocketSessionController` intentionally emits raw unmasked payloads. Masking policies for sensitive headers and payload tokens must be applied in the presenter and export layers (WS-4 / PYPOST-1130 and WS-6 / PYPOST-1132) before rendering or exporting.
2. **Error Category Extraction**:
   - `QtWebSocketTransport._on_error_occurred` resolves error categories via `getattr(error, "name", "socket_error")`. While reliable across PySide6 socket error enums, mapping to a formal, unified domain error enum in `websocket_session_policy.py` would improve typed pattern matching across protocols.
3. **Subprotocol Handling**:
   - Multiple requested subprotocols are passed directly to `QWebSocketHandshakeOptions.setSubprotocols()`. Server negotiation validation is delegated to Qt's native implementation; custom subprotocol negotiation policies (e.g., custom GraphQL-WS vs GraphQL-Transport-WS fallback) are deferred to higher-level protocol handlers.

## Missing Tests

While all 18 unit, architectural isolation, and loopback integration tests pass with 100% code coverage across the 4 modules, the following boundary scenarios will be expanded in the dedicated test harness task (WS-11 / PYPOST-1137):
1. **Network Chaos & Socket Edge Cases**:
   - Sudden TCP RST packets without FIN handshakes.
   - Half-open socket detection and stale connection timeout behaviors.
   - Fragmented multi-frame bursts and malformed UTF-8 byte sequences.
2. **Complex TLS / PKI Scenarios**:
   - Self-signed certificates, untrusted root CAs, and hostname mismatches with explicit bypass verification.
   - Mutual TLS (mTLS) client certificate negotiation.
   - Intermediate certificate chain verification and revocation checking (CRL/OCSP).
3. **High-Throughput Load & Concurrency**:
   - Sustained multi-thousand frame/sec throughput benchmarks to profile garbage collection overhead.
   - Proxy traversal (HTTP CONNECT proxies and SOCKS5).

*Note: All existing test files in `tests/test_websocket_*.py` include explicit pytest timeouts (`pytestmark = pytest.mark.timeout(30)`).*

## Performance Concerns

1. **Frame Allocation Throughput & GC Pressure**:
   - For every incoming and outgoing message frame, a new immutable `RawFrame` dataclass and `datetime.now(timezone.utc)` instance are created, followed by a Qt signal emission (`Signal(object)`). In continuous high-speed streaming (>10,000 frames/second), frequent object allocations may increase Python garbage collection overhead.
2. **Main Thread Event Loop Utilization**:
   - `PySide6.QtWebSockets.QWebSocket` runs on the Qt GUI/event loop thread. Converting large binary payloads (`QByteArray` to `bytes`) on the main thread for message frames up to 16MB can consume main thread execution cycles. Stream ingestion offloading in WS-3 will mitigate this for large payloads.

## Follow-up Tasks

The following downstream tasks in the WebSocket Epic (PYPOST-1124) address the architectural extensions and integration points:
- **PYPOST-1128 (WS-2)**: WebSocket Session Persistence & SQLite Metadata Store — persist session states, handshake parameters, and frame logs to disk.
- **PYPOST-1129 (WS-3)**: High-Throughput Circular Streaming Ring Buffer — implement fixed-capacity ring buffer with sliding-window search and filtering.
- **PYPOST-1130 (WS-4)**: WebSocket UI Presenter & Inspector — connection status indicator, live streaming timeline, frame inspector, and message composer widgets.
- **PYPOST-1132 (WS-6)**: Sensitive Data Masking Policies — redact sensitive headers, bearer tokens, and configurable regex patterns in WebSocket frame streams.
- **PYPOST-1137 (WS-11)**: Automated WebSocket Mock Server & Test Harness — hermetic test harness with network fault injection, fuzzing, and proxy support.
