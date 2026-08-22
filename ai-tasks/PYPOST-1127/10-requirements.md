# PYPOST-1127: WS-1 WebSocket transport seam and Qt-native session engine

## Goals

PyPost is expanding beyond HTTP request/response interactions to support real-time, stateful, bidirectional WebSocket communication (Epic PYPOST-1123). Before building user interfaces, persistent collection models, message stream views, or agent-facing MCP tools, PyPost requires a robust, testable, headless networking and session engine.

The goal of this task is to provide the non-visual networking foundation for all WebSocket capabilities in PyPost:
- A Qt-free transport protocol abstraction (`WebSocketTransport`, `WebSocketTransportListener`) ensuring architectural decoupling and engine reversibility.
- A pure, testable state machine and lifecycle policy for session transitions, heartbeat pings/pongs, and backoff reconnection schedules.
- A Qt-native transport adapter using `PySide6.QtWebSockets.QWebSocket` that runs on the existing Qt event loop without blocking or requiring extra worker threads.
- A decoupled session controller (`WebSocketSessionController`) that orchestrates session lifecycles, emits raw unmasked frames, and maintains zero coupling to UI widgets, message streams, or environment masking logic.

This story establishes the verified transport and session baseline that every subsequent WebSocket story (WS-2 through WS-12) builds upon.

**Implementation language**: Python (targeting Python 3.11+ and the existing PySide6 6.11+ runtime stack; Qt-free core protocols with a single QtWebSockets adapter in `pypost/core/qt/`).

## User Stories

- **As a PyPost developer building WebSocket features (WS-3..WS-10)**, I want a clean, event-driven session controller with explicit lifecycle signals and raw frame emission, so that I can implement stream buffers, tab presenters, and MCP probe tools on top of a proven, decoupled engine.
- **As an API developer testing WebSocket services**, I want PyPost's connection engine to reliably negotiate subprotocols, exchange text and binary frames, maintain heartbeats, and handle network disconnects with backoff retries, so that my real-time testing sessions remain stable and predictable.
- **As an automated testing / QA engineer**, I want to execute WebSocket session tests headlessly and offline against local fixtures without requiring a graphical display or mock UI widgets, so that the session engine's reliability can be verified continuously in CI.
- **As a software architect**, I want `PySide6.QtWebSockets` imports strictly confined to a single adapter behind a Qt-free protocol seam, so that networking engine decisions remain reversible without rewriting session policy, stream management, or UI layers.

## Definition of Done

This task is considered done when the following acceptance criteria are fully met and verified by automated tests:

1. **Successful Handshake & Subprotocol Negotiation**:
   Connecting to a WebSocket endpoint reaches the `Open` state and accurately reports any negotiated subprotocol.
2. **Bidirectional Full-Duplex Data Transfer**:
   Text and binary messages reliably round-trip in both directions without corruption or frame loss.
3. **Graceful Server-Initiated Closure**:
   When the server initiates connection closure, the session transitions cleanly to `Closed`, surfacing the exact numeric close code (e.g. 1000, 1001) and reason string verbatim.
4. **Specific Handshake Rejection Handling**:
   A rejected handshake or failed connection surfaces a descriptive, specific failure reason (not a generic "connection failed" message) and transitions the session cleanly to `Failed`.
5. **Heartbeat Monitoring & Timeout**:
   Heartbeat pings are dispatched at configured intervals; if a corresponding pong is not received within the configured timeout window, the session terminates with failure reason `heartbeat_timeout`.
6. **Automatic Bounded Reconnection**:
   When an established connection drops unexpectedly, the engine automatically retries connection using the configured backoff schedule (initial delay, multiplier, max delay, max attempts). Progress is emitted per attempt, and if max attempts are exceeded, the session ends in `Failed` with `reconnect_exhausted` with no further retries.
7. **Incoming Message Size Enforcement**:
   The configured maximum incoming message size (`ws_max_incoming_message_bytes`) is enforced directly at the transport level; incoming frames exceeding this bound abort/close the session with an explanatory error instead of attempting unbounded memory allocation.
8. **Deterministic Resource Cleanup**:
   Closing or destroying a session controller releases the underlying transport socket and ensures no lingering `QObject`, timers, or threads remain active in memory.
9. **Import Isolation Guard**:
   An automated architectural guard test verifies that `PySide6.QtWebSockets` is imported exclusively within `pypost/core/qt/websocket_transport.py` and nowhere else in the codebase.
10. **Signal/Callback Ordering Pinning**:
    The exact relative ordering of the transport's opened callback and socket state change events is explicitly pinned and verified by automated tests (resolving Open Question OQ-1 from PYPOST-1124).
11. **Strict Controller Decoupling**:
    An automated test asserts that `pypost/core/qt/websocket_session.py` does not import `websocket_stream`, `Environment`, or secret masking policies, and that frames emitted by the controller reach listeners unmodified and unmasked as `RawFrame` objects.

## Task Description

PYPOST-1127 is the first engineering story (WS-1, Wave 1) of Epic PYPOST-1123, implementing the core transport abstraction and Qt-native WebSocket session engine designed in RFC PYPOST-1124 (specifically architecture section A-13.1).

### Scope
- `pypost/core/websocket_transport_protocol.py`: Qt-free `WebSocketTransport` and `WebSocketTransportListener` protocols, `HandshakeTarget` dataclass, and `RawFrame` dataclass.
- `pypost/core/websocket_session_policy.py`: Pure, Qt-free state machine definitions (`SessionState`), reconnect backoff scheduling, and heartbeat policy rules.
- `pypost/core/qt/websocket_transport.py`: Sole `QWebSocket` transport adapter implementing `WebSocketTransport`.
- `pypost/core/qt/websocket_session.py`: `WebSocketSessionController(QObject)` coordinating state transitions, heartbeat/reconnect timers, and signal emissions.
- Unit and integration test suite verifying connection lifecycle, frame roundtripping, heartbeat, reconnection, error handling, and architectural import boundaries.

### Out of Scope
- User interface components, widgets, tabs, inspectors, and composers (covered in WS-4, WS-5, WS-6).
- Connection profile persistence, models, collection storage, and import/export (covered in WS-2).
- Bounded stream ring buffer, eviction policy, codecs, and stream export (covered in WS-3).
- Environment variable templating and sensitive data masking in the UI (covered in WS-7).
- Custom TLS certificates, untrusted CA handling, and TLS user prompts (covered in WS-8).
- Model Context Protocol (MCP) WebSocket probe tool (covered in WS-9).
- Global settings, session concurrency limits, Prometheus metrics, and system logging (covered in WS-10).

## Functional Requirements

- **FR-1: Transport Protocol Seam**:
  - Provide a Qt-free `WebSocketTransport` protocol defining `open`, `send_text`, `send_binary`, `ping`, `close`, `abort`, `negotiated_subprotocol`, and `set_listener`.
  - Provide a `WebSocketTransportListener` protocol for receiving callbacks: `on_opened`, `on_text`, `on_binary`, `on_pong`, `on_closed`, `on_failed`, and `on_tls_errors`.
  - Accept connection parameters via an immutable `HandshakeTarget` object containing URL, custom headers, subprotocol candidates, message size limits, and TLS verification flags.
- **FR-2: Session State Machine & Lifecycle**:
  - Support formal session states: `Idle`, `Connecting`, `Open`, `Closing`, `Closed`, `Reconnecting`, and `Failed`.
  - Emit clear state change notifications with relevant detail metadata (e.g. status descriptions, error categories).
  - Guarantee that manual cancellation/close requests transition the session through `Closing` to `Closed` deterministically.
- **FR-3: Duplex Data Transmission**:
  - Send and receive UTF-8 text messages and raw binary payloads.
  - Re-emit incoming and outgoing messages as unmasked `RawFrame` structures containing direction (`IN` / `OUT`), format (`text` / `binary`), payload, and byte size.
- **FR-4: Heartbeat & Health Monitoring**:
  - Periodically dispatch ping frames according to configured heartbeat intervals.
  - Track pong response latency.
  - Trigger immediate session termination with `heartbeat_timeout` when a pong fails to arrive within the timeout threshold.
- **FR-5: Bounded Reconnection Strategy**:
  - Automatically detect unexpected socket disconnects when reconnection policy is enabled.
  - Calculate exponential backoff delays with jitter/bounds up to `max_delay_seconds`.
  - Re-attempt connection up to `max_attempts`, emitting `reconnect_scheduled(attempt, max_attempts, delay_ms)` before each retry.
  - Transition to `Failed` with `reconnect_exhausted` when attempts are depleted.
- **FR-6: Resource & Socket Management**:
  - Ensure closing a controller completely frees the socket and stops all associated QTimers.
  - Never leak background threads or orphaned QObjects on session completion or failure.

## Non-Functional Requirements

- **NFR-1: Performance & Responsiveness**:
  - Non-blocking execution leveraging Qt's asynchronous socket event loop; no worker threads required for socket I/O.
  - Frame delivery must occur with minimal overhead without copying frame data unnecessarily.
- **NFR-2: Reliability & Error Diagnostics**:
  - Handshake rejections, network errors, and protocol violations must capture actionable error strings directly from the transport rather than masking them behind generic error messages.
- **NFR-3: Architectural Isolation & Modularity**:
  - Layering compliance: `pypost/core/` remains strictly Qt-free.
  - All `PySide6.QtWebSockets` usage is quarantined in `pypost/core/qt/websocket_transport.py`.
  - `WebSocketSessionController` must hold no reference to UI widgets, `MessageStream`, or secret masking environments.
- **NFR-4: Testability**:
  - The session engine and state policy must be testable headlessly in CI under `QT_QPA_PLATFORM=offscreen`.
  - Unit tests for `websocket_session_policy.py` must run without requiring a `QApplication` or event loop.

## Main Entities

- **HandshakeTarget**: Immutable data structure encapsulating resolved connection targets (URL, headers, subprotocols, TLS verify flag, max incoming message size).
- **RawFrame**: Low-level transport frame representation capturing transmission direction (`IN` / `OUT`), payload format (`text` / `binary`), payload data, and byte length.
- **WebSocketTransport**: Protocol defining the low-level asynchronous socket interface.
- **WebSocketTransportListener**: Protocol for receiving asynchronous transport events and frames.
- **WebSocketSessionPolicy / State Machine**: Pure logic component managing state transitions, backoff schedules, and heartbeat triggers.
- **WebSocketSessionController**: QObject coordinator binding the transport adapter and session policy, managing timers, and exposing Qt signals to presenters.

## User Scenarios

1. **Successful Connect, Exchange, and Disconnect**:
   - A caller configures a `HandshakeTarget` with an echo endpoint and invokes `open()`.
   - The session enters `Connecting`, the socket handshakes, and transitions to `Open` with the negotiated subprotocol reported.
   - The caller sends a text message and a binary frame; the echo server echoes both; `frame_sent` and `frame_received` signals emit corresponding `RawFrame` instances.
   - The caller invokes `close(1000, "Normal Closure")`; the session enters `Closing` then `Closed`.
2. **Server-Initiated Close**:
   - During an active `Open` session, the remote server closes the connection with code `1001` ("Going Away").
   - The controller receives the transport event, transitions state to `Closed`, and emits `lifecycle_event` with code `1001` and reason "Going Away".
3. **Handshake Rejection / Authentication Failure**:
   - A caller attempts to connect to an endpoint requiring authorization without providing valid headers.
   - The server rejects the handshake; the transport captures the specific socket error string and fires `on_failed`.
   - The controller enters `Failed` with the exact error details and does not attempt reconnection.
4. **Heartbeat Timeout on Unresponsive Peer**:
   - An active session with a 5-second heartbeat interval and 2-second timeout stops receiving pong responses from an unresponsive peer.
   - The heartbeat timer triggers a timeout; the controller immediately aborts the transport and transitions to `Failed` with `heartbeat_timeout`.
5. **Dropped Connection with Successful Automatic Reconnect**:
   - An active connection is abruptly terminated due to a transient network glitch.
   - The policy recognizes an unexpected disconnect with reconnect enabled; the controller transitions to `Reconnecting` and schedules an attempt with initial backoff.
   - When the backoff timer expires, a fresh transport instance connects successfully; state returns to `Open` and session communication resumes.
6. **Reconnection Attempts Exhausted**:
   - A remote server permanently goes offline during an active session.
   - The controller retries connection up to `max_attempts` with exponential backoff delays.
   - Upon the final failure, the controller enters `Failed` with reason `reconnect_exhausted` and halts all timers.
7. **Incoming Message Exceeds Buffer Limit**:
   - The remote peer sends a frame larger than `max_incoming_message_bytes`.
   - The transport detects the violation, aborts the socket, and reports a message size violation failure.

## Q&A

| Question | Answer |
| --- | --- |
| Why is this implemented with `PySide6.QtWebSockets` rather than `websockets` (asyncio)? | `PySide6.QtWebSockets` is already shipped within the pinned PySide6 distribution (`pyside6-addons`), requiring zero new production dependencies. It runs directly on Qt's native event loop without adding worker threads or complex cross-thread synchronization (RFC PYPOST-1124 D-1). |
| Why does `WebSocketSessionController` not own the message stream ring or secret masking? | Separation of concerns: the controller is a headless engine responsible only for connection lifecycle, state machine, and raw frame transport. Message stream buffering (WS-3) and secret masking (WS-7) belong to the presentation and UI layers (RFC PYPOST-1124 A-3.1). |
| Why is a transport protocol seam needed if Qt is the primary engine? | The `WebSocketTransport` protocol ensures that the networking engine remains decoupled and reversible. If an alternative transport (e.g. asyncio or custom C++ client) is required in the future, it can be swapped without modifying session controllers, presenters, or UI code. |
| How are unit tests run without external networks? | Tests run hermetically against local `QWebSocketServer` fixtures (WS-11 test harness) under `QT_QPA_PLATFORM=offscreen`, requiring no public internet access or physical display. |
