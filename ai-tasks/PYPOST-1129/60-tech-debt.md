# PYPOST-1129: Technical Debt Analysis

**Verdict:** In-process scripted WebSocket test server (`tests/websocket_echo_server.py`), fixture (`tests/conftest.py`), and test suite (`tests/test_websocket_echo_server.py`) meet all architectural requirements and Definition of Done. All 17 unit/integration tests pass with explicit pytest timeout markers and bounded event-loop polling. Zero leaked ports or sockets.
**SAFE TO CLOSE.** Follow-up items below are non-blocking enhancements and subsequent story integrations.

Scope reviewed:
- `tests/websocket_echo_server.py` (`ServerBehavior`, `ServerBehaviorConfig`, `ScriptedWebSocketServer`)
- `tests/conftest.py` (`ws_test_server` fixture)
- `tests/test_websocket_echo_server.py` (17 tests covering startup, lifecycle, behaviors, flood, leak checks, observability)
- `pypost/core/qt/websocket_transport.py` (enum compatibility fixes for Qt6 / PySide6)
- `ai-tasks/PYPOST-1129/*` (requirements, architecture, cleanup, observability)

---

## Shortcuts Taken

1. **Non-Secure (`ws://`) Mode Only (Architectural Boundary)**:
   - The test server initializes `QWebSocketServer` with `QWebSocketServer.SslMode.NonSecureMode` (`ws://` only).
   - TLS / `wss://` encrypted test mode with ephemeral self-signed SSL certificates and custom trust anchors is intentionally decoupled and owned by story **WS-8 (PYPOST-1134: TLS policy & secure WebSocket handling)** per the Wave 0 architectural plan in `ai-tasks/PYPOST-1124/20-architecture.md`.
2. **Single-Threaded In-Process Execution**:
   - `ScriptedWebSocketServer` runs directly within the Qt event loop on the main test thread rather than spawning a dedicated background worker thread or external daemon process.
   - *Rationale:* Eliminates thread-synchronization race conditions, enables deterministic Qt signal/slot event delivery with `wait_until()` and `QCoreApplication.processEvents()`, and ensures zero-overhead teardown.
   - *Trade-off:* Test callbacks executed inside `CUSTOM_CALLBACK` must remain non-blocking to prevent stalling the Qt event loop.
3. **Fixed Flood String Payload**:
   - `ScriptedWebSocketServer.flood(count, size)` emits repeated character strings (`"A" * size`).
   - Binary fuzzing or randomized frame stream generators are not built-in, though `CUSTOM_CALLBACK` and `send_to_all()` allow custom payload injection when required by downstream tests.

---

## Code Quality Issues

1. **Direct Signal Lambdas in Connection Listener**:
   - In `ScriptedWebSocketServer._on_new_connection`, signal lambdas (`lambda msg, c=client: self._on_text_message_received(c, msg)`) are bound dynamically to per-client signals.
   - *Improvement:* While concise and effective for test infrastructure, encapsulating client connections into dedicated helper structs or named slot adapters could simplify signal disconnection tracking.
2. **Socket Deletion on Disconnect**:
   - In `_on_client_disconnected`, disconnected client sockets are removed from `self._clients`, relying on Qt's object hierarchy and Python garbage collection for final reclamation.
   - *Improvement:* Adding an explicit `client.deleteLater()` call upon disconnection ensures immediate C++ Qt object destruction under high connection churn.
3. **Symmetrical Auto-Trigger for Oversize Messages**:
   - `CLOSE_WITH_CODE` includes a `close_on_connect: bool = True` option, whereas `OVERSIZE_MESSAGE` is currently triggered via test calls to `send_to_all()`.
   - *Improvement:* Adding `oversize_on_connect: bool = False` to `ServerBehaviorConfig` would make all scripted behavior triggers fully declarative and symmetrical.

---

## Missing Tests

| Scenario | Status | Notes |
| -------- | ------ | ----- |
| Dynamic loopback ephemeral port binding (`127.0.0.1:0`) | **Present** | Tested in `test_server_startup_binding_and_properties` |
| Context manager lifecycle (`__enter__`, `__exit__`) | **Present** | Tested in `test_server_context_manager` |
| Pytest fixture lifecycle (`ws_test_server`) | **Present** | Tested in `test_ws_test_server_fixture_lifecycle` |
| Text & binary echo exchange | **Present** | Tested in `test_behavior_echo_text_and_binary` |
| Handshake rejection (CORS / HTTP 403) | **Present** | Tested in `test_behavior_reject_handshake` |
| Subprotocol negotiation & refusal | **Present** | Tested in `test_behavior_subprotocol_negotiation_and_refusal` & `test_behavior_subprotocol_refuse` |
| Custom close code (RFC 6455) & reason delivery | **Present** | Tested in `test_behavior_close_with_code_and_reason` |
| Silent server (heartbeat / ping suppression) | **Present** | Tested in `test_behavior_silent_server_suppresses_replies` |
| High-throughput flood message emission | **Present** | Tested in `test_behavior_flood_burst` |
| Oversize frame delivery | **Present** | Tested in `test_behavior_oversize_message_delivery` |
| Abrupt midstream TCP connection drop | **Present** | Tested in `test_behavior_midstream_connection_drop` |
| Custom callback response injection | **Present** | Tested in `test_behavior_custom_callback` |
| Leak-free repeated startup/teardown cycles | **Present** | Tested in `test_repeated_startup_teardown_leak_free` |
| Offscreen event loop responsiveness under load (<50ms lag) | **Present** | Tested in `test_offscreen_responsiveness_under_load` |
| Observability counters & buffer reset | **Present** | Tested in `test_observability_counters_and_buffers` |
| Structured key-value logging output | **Present** | Tested in `test_observability_structured_logging` |
| Multi-client selective message targeting | Optional (TD-1) | Non-blocking enhancement for future multi-session testing |
| TCP-level frame chunking/fragmentation simulation | Out of Scope | Qt handles frame reassembly; low-level TCP chunking out of scope |

### Timeout Marker Review
- **BLOCKER Check**: Every test in `tests/test_websocket_echo_server.py` declares an explicit `@pytest.mark.timeout(...)` annotation and a module-level `pytestmark = pytest.mark.timeout(15)`.
- **Result**: **NO BLOCKER** — 100% compliant with `do-testing` requirements.

---

## Performance Concerns

1. **Unbounded Message History Buffers**:
   - `ScriptedWebSocketServer` stores received and sent messages in unbounded in-memory lists (`_received_messages`, `_sent_messages`, etc.).
   - *Impact:* In extreme stress tests emitting >100,000 messages, memory consumption could grow.
   - *Mitigation:* `reset()` clears all buffers between tests; adding an optional `max_history: Optional[int] = None` parameter in the future would enforce ring-buffer truncation for long benchmarks.
2. **Synchronous Loop During Flooding**:
   - `flood(count, size)` broadcasts frames inside a single Python loop.
   - *Impact:* For very large bursts (>5,000 frames), backpressure in Qt's internal socket write queues could delay event processing.
   - *Mitigation:* Verified in `test_offscreen_responsiveness_under_load` that standard bursts (50–100 messages) complete in <50ms without event loop lag.

---

## Follow-up Tasks

### Upstream / Epic Follow-up Stories
1. **PYPOST-1130 (WS-1)**: Implement `WebSocketTransport` and `WebSocketSession` client classes and verify connection lifecycle using `ws_test_server`.
2. **PYPOST-1134 (WS-8)**: Implement TLS / `wss://` secure WebSocket server support with ephemeral self-signed certificates and SSL configuration fixtures.

### Technical Debt Improvements (Non-blocking)
3. **TD-1 (Low)**: Add `send_to_client(client, message)` helper and explicit `client.deleteLater()` on client disconnection in `ScriptedWebSocketServer`. Jira: [PYPOST-1139](https://pypost.atlassian.net/browse/PYPOST-1139) (1 SP)
4. **TD-2 (Low)**: Add optional `max_history` buffer truncation parameter to `ScriptedWebSocketServer` to prevent memory growth during large-scale benchmarks. Jira: [PYPOST-1140](https://pypost.atlassian.net/browse/PYPOST-1140) (1 SP)

---

## Blocker Review

| Check | Result |
| ----- | ------ |
| Temporary solutions / crutches | None blocking release; non-secure mode is intentional per Wave 0 architecture |
| Missing tests with timeout markers | **None** — 100% of tests have explicit `@pytest.mark.timeout(...)` |
| Deviations from architecture | **None** — full alignment with `ai-tasks/PYPOST-1124/20-architecture.md` (WS-11) |
| Acceptance gaps vs DoD | **None** — all 6 DoD criteria completely satisfied |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** for PYPOST-1129.
