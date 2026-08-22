# PYPOST-1129: WS-11 WebSocket test harness

## Goals

Epic PYPOST-1123 introduces WebSocket protocol support to PyPost, replacing the one-shot HTTP request/response model with a persistent bidirectional communication model. To deliver and maintain this major capability reliably across all implementation stories (WS-1 through WS-10), the development workflow requires automated testing infrastructure that operates entirely offline, deterministically, and headlessly.

**Why a dedicated test harness is needed (the business reason):**
1. **Offline and Isolated Verification**: Tests must never rely on external third-party WebSocket endpoints or public internet services. Public endpoints introduce network latency, rate limits, unannounced downtime, internet connectivity requirements, and flakiness into CI/CD pipelines. An in-process, self-contained test server guarantees 100% offline test execution.
2. **Deterministic Simulation of Protocol & Failure Scenarios**: Real-world WebSocket interactions include complex edge cases—handshake rejections, subprotocol negotiation mismatches, silent connection loss, sudden socket drops, oversize message frames, and abnormal close codes. Verifying that the client handles these transitions gracefully requires a test harness capable of scripted, reproducible server behaviors.
3. **Continuous Integration & Headless Performance**: Automated test suites in CI containers run without a physical display server (`QT_QPA_PLATFORM=offscreen`). The test fixture must seamlessly support headless execution, guarantee fast startup and teardown, and strictly prevent resource leaks (such as hanging threads or orphaned listening ports).
4. **Performance & Responsiveness Safeguards**: High-frequency streaming must not degrade the responsiveness of the application or violate memory budgets. The test harness provides the foundation for performance flood testing to establish latency and buffer retention bounds before user-facing UI stories merge.

**Programming language:** Python. All test infrastructure and helper utilities will be implemented in Python matching the PyPost codebase standards.

## User Stories

### US-1: Offline Client Protocol Verification
**As a** developer implementing WebSocket client features (transport, session controller, stream inspector, composer, MCP probe),  
**I want** an in-process local WebSocket server fixture that starts and stops automatically per test,  
**So that** I can test connection establishment, frame exchange, and disconnection offline without external network dependencies.

### US-2: Scripted Error and Edge-Case Simulation
**As a** test engineer,  
**I want** the test fixture to simulate scripted server behaviors (such as handshake rejections, subprotocol negotiation/refusal, custom close codes and reasons, silence during heartbeats, oversize frames, and abrupt connection drops),  
**So that** I can deterministically verify client error handling, reconnection policies, and failure diagnostics.

### US-3: Clean Resource Management in CI
**As a** CI/CD pipeline maintainer,  
**I want** the test harness to guarantee clean lifecycle teardown with bounded timeouts and zero leaked ports or background threads,  
**So that** test runs remain fast, deterministic, and isolated without wedging subsequent test runs or hanging CI jobs.

### US-4: UI Responsiveness and Buffer Bound Verification
**As a** performance engineer,  
**I want** automated flood testing capabilities that evaluate client behavior under high message throughput,  
**So that** we can ensure the retained message budget holds and the event loop responsiveness stays within documented latency bounds.

## Definition of Done

The task is considered done when the following acceptance criteria are fulfilled:

1. **Local Test Fixture Availability**:
   - A dedicated local WebSocket server fixture is implemented and registered in the test configuration (`tests/conftest.py`).
   - The server binds dynamically to `127.0.0.1:0` (ephemeral port) to avoid port collisions during concurrent test execution.

2. **Scripted Behaviors**:
   The test harness supports configuring and executing scripted server scenarios:
   - **Echo**: Standard echoing of incoming text and binary frames.
   - **Handshake Rejection**: Simulated handshake failure (e.g. invalid credentials or server errors).
   - **Subprotocol Handling**: Negotiating requested subprotocols or refusing unsupported subprotocols.
   - **Controlled Closure**: Closing connections with configurable RFC 6455 close codes (e.g., 1000, 1001, 1008, 1011) and custom reason strings.
   - **Silent Server (Heartbeat Testing)**: Suppressing responses/pongs to test client heartbeat timeouts and ping monitors.
   - **Message Flood**: Generating bursts of messages at configurable rates to stress test intake pipelines.
   - **Oversize Frame**: Sending messages exceeding standard frame/message size limits to verify client truncation/rejection safeguards.
   - **Mid-stream Disconnect**: Abruptly dropping underlying TCP connections to verify connection-lost detection and auto-reconnect triggers.

3. **Lifecycle and Leak Prevention**:
   - The test server starts and stops reliably within bounded time per test.
   - Zero socket, port, or thread leaks across repeated fixture startup/teardown cycles.

4. **Deterministic Synchronization**:
   - Integration with bounded-wait event polling helpers (leveraging `pypost/agent/ui_wait.py`) so tests synchronize on event conditions rather than arbitrary `time.sleep` calls.

5. **Strict Test Environment Compliance**:
   - Zero network calls to public internet endpoints across all test cases.
   - Every test case declares an explicit `pytest.mark.timeout(...)` annotation.
   - All tests pass in headless mode with `QT_QPA_PLATFORM=offscreen`.

6. **Responsiveness and Flood Verification**:
   - A dedicated flood test validates that the client's retained message byte budget is respected and GUI event-loop responsiveness remains within acceptable latency limits under high throughput.
   - The flood test is marked with `pytest.mark.slow` if execution time exceeds the fast test suite budget.

## Task Description

### Background and Context
PyPost architectural plan for WebSocket support ([`ai-tasks/PYPOST-1124/20-architecture.md`](../PYPOST-1124/20-architecture.md), section A-13.11) specifies that the test harness (WS-11) is the foundational "Wave 0" deliverable of Epic PYPOST-1123. All subsequent implementation stories (WS-1 transport, WS-2 models, WS-3 stream buffer, WS-4 tab, WS-5 stream inspector, WS-6 composer, WS-7 env/masking, WS-8 TLS, WS-9 MCP probe, WS-10 metrics/settings) rely on this harness for automated verification.

### System Boundaries & Scope
- **In Scope**:
  - Implementation of the local WebSocket test server utility (`tests/websocket_echo_server.py`).
  - Configuration of scripted server behaviors (echo, rejection, subprotocol negotiation/refusal, close codes, silence, flood, oversize messages, socket drops).
  - Integration of bounded-wait mechanisms for deterministic test assertions.
  - Registration of the fixture in `tests/conftest.py` for global test suite access.
  - Development of flood and responsiveness tests (`tests/test_websocket_flood.py`) verifying memory retention and event-loop latency.
- **Out of Scope**:
  - Production code changes inside the `pypost/` package.
  - TLS / `wss://` encrypted server mode (owned and provided by story WS-8).
  - Client UI widgets and presenters (owned by stories WS-4, WS-5, WS-6).

### Main Business Entities

```
+-------------------------------------------------------------+
|                     Test Server Fixture                     |
|  - Binds to 127.0.0.1:0 (ephemeral port)                   |
|  - Manages startup, client connection hooks, and teardown   |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                  Scripted Server Behaviors                  |
|  - Echo (text & binary)        - Silence (heartbeat test)   |
|  - Handshake Rejection         - Message Flood Generator    |
|  - Subprotocol Negotiate/Refuse- Oversize Message Delivery  |
|  - Custom Close (code, reason) - Mid-stream Connection Drop |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                   Test Synchronization & Probes             |
|  - Bounded Wait Helper (event processing deadline)          |
|  - Responsiveness Probe (GUI latency measurement)           |
|  - Retention Budget Probe (byte/message limit assertion)    |
+-------------------------------------------------------------+
```

- **Test Server Fixture**: The controller managing the in-process server instance, lifecycle hooks, and port binding.
- **Scripted Server Behavior**: A configurable behavior profile governing how the server responds during handshakes, message reception, and connection lifecycle events.
- **Bounded Wait Helper**: Synchronization coordinator that drives event processing until expected conditions are satisfied or a deadline expires.
- **Responsiveness & Budget Probe**: Metric collector measuring event loop lag and buffer retention during stress tests.

### Non-Functional Requirements
- **Determinism**: 100% repeatable outcomes across local developer workstations and CI runners.
- **Isolation**: Each test runs against an isolated server instance or reset state; no state leakage or shared socket pollution across tests.
- **Speed & Efficiency**: Server setup and teardown overhead must be minimal (milliseconds) to keep the fast test suite responsive.
- **Headless Compatibility**: Operates without a physical display environment (`QT_QPA_PLATFORM=offscreen`).

## Q&A

**Q: Why does the test harness bind to `127.0.0.1:0` instead of a fixed port (e.g. 8080 or 9001)?**  
A: Binding to port `0` allows the operating system to allocate an ephemeral free port. This prevents port collision conflicts when running test suites in parallel or on shared build machines where a static port might already be in use.

**Q: Why is TLS server testing excluded from WS-11?**  
A: Per the architectural breakdown in `ai-tasks/PYPOST-1124/20-architecture.md` (section A-13.11 and A-13.8), TLS certificate configuration and SSL policy testing are isolated to story WS-8 (TLS policy), which supplies its own TLS certificates and test setup. WS-11 focuses on standard WebSocket protocol mechanics and failure modes.

**Q: Why is a bounded-wait helper mandatory rather than using `time.sleep(...)` in tests?**  
A: `time.sleep(...)` in UI and event-driven testing either causes flaky failures when the sleep duration is too short or unnecessarily slows down CI runs when padded with generous delays. Bounded event polling with `wait_until` polls the condition while actively processing Qt events and returns immediately upon condition resolution.

**Q: What is the relationship between WS-11 and the other WebSocket stories?**  
A: WS-11 is the prerequisite Wave 0 story. Delivering WS-11 first ensures that every client story (WS-1 session engine, WS-2 persistence, WS-3 ring buffer, WS-4 tab, WS-5 stream inspector, WS-6 composer, WS-7 masking, WS-9 MCP probe, WS-10 metrics) can be verified headlessly and offline from its very first commit.
