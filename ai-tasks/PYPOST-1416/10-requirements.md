# PYPOST-1416: Live Wire IPC and Stdio Transport Stress Testing for Standalone MCP Servers

## Goals

In modern developer workflows, PyPost standalone Model Context Protocol (MCP) servers function as external execution backends that communicate with diverse AI agents, IDE extensions, and automation tools across operating system boundaries. In production environments, client agents communicate with these standalone servers over real operating system communication channels: loopback network sockets (TCP/HTTP/SSE) and standard input/output (stdio) pipelines.

Previous verification phases (such as in [PYPOST-1410](file:///home/src/ai-tasks/PYPOST-1410/10-requirements.md) and [PYPOST-1412](file:///home/src/ai-tasks/PYPOST-1412/10-requirements.md)) verified server lifecycle state transitions and collection variable resolution in-process using direct programmatic invocations. However, in-process assertions bypass the physical transport layer entirely. They do not exercise:
1. Real wire-level message framing and chunked data serialization.
2. Kernel socket buffering, pipe flow control, or backpressure under high volume.
3. TCP packet fragmentation and boundary reassembly when payloads exceed network MTU sizes.
4. Concurrency contention when multiple clients or bursts of requests arrive simultaneously.
5. Operating system resource hygiene (process termination, descriptor reclamation, avoiding hung descriptors or zombie processes).

Without dedicated live wire stress testing, real-world deployment risks subtle, catastrophic failures: servers hanging under burst traffic, dropping fragmented packets, deadlocking on full stdio pipe buffers, leaking open file descriptors, or failing to cleanly shut down after an agent disconnects.

The business goal of this task is to establish a rigorous, live wire stress-testing verification suite for standalone MCP servers. This ensures that PyPost standalone servers operate reliably under sustained real-world load across loopback TCP sockets and stdio pipes, guaranteeing message integrity, deterministic protocol negotiation, robust concurrency, and leak-free lifecycle teardown.

## Programming Language

- **Implementation language**: Python

## User Stories

- As an **AI agent or IDE client**, I want to exchange high-frequency JSON-RPC messages with PyPost standalone MCP servers over real TCP sockets and stdio pipes without message corruption or lost frames, so that automated workflows execute predictably without network timeouts or transport-level resets.
- As an **API engineer / developer**, I want standalone MCP servers to process large payloads and sustained multi-message bursts across fragmented packet boundaries without deadlocking or dropping requests, so that data-intensive tool calls succeed consistently under production loads.
- As a **DevOps / platform operator**, I want standalone server processes and communication channels to clean up deterministically upon shutdown without orphan processes, zombie threads, or hung socket descriptors, so that system resources are preserved and local ports remain immediately reusable.
- As a **QA / automated test engineer**, I want wire-level stress tests that execute deterministically within strict test timeout boundaries without flaky failures or uncoordinated port collisions, so that CI/CD pipelines provide reliable quality gating.

## Definition of Done

This task is considered complete when:
1. A live wire stress-testing suite is established that exercises standalone MCP servers over physical loopback TCP sockets and OS stdio communication streams without in-memory mocks or simulated transports.
2. Complete MCP protocol lifecycle sequences are verified over the wire:
   - Client initialization handshake and capability negotiation.
   - Dynamic tool discovery and schema exchange.
   - Concurrent tool invocation and response delivery.
   - Graceful client disconnection and server session finalization.
3. Wire framing and message integrity verification passes under stress:
   - Chunked and fragmented TCP packets reassemble correctly without malformed framing errors.
   - Large message payloads (exceeding typical socket buffer sizes) transmit and parse without truncation or corruption.
   - Multi-message bursts arriving back-to-back in rapid succession parse deterministically.
4. Sustained throughput and concurrency requirements are verified:
   - Server processes continuous request bursts under sustained concurrency without dropped connections, socket stalls, or message loss.
   - Minimum verifiable throughput rates are met under load without unbounded latency growth.
5. Clean lifecycle teardown and resource reclamation are verified:
   - Terminating server sessions cleanly closes OS pipe descriptors and releases loopback TCP ports without leaving sockets stuck in lingering states or leaking open file handles.
   - Child processes and background execution threads exit completely without creating zombie processes or orphan threads.
6. Test reliability and execution constraints comply with project standards:
   - All tests enforce bounded timeouts per repository testing contracts.
   - Port allocations avoid conflicts and teardown fixtures ensure zero cross-test environment contamination.
7. Verification passes all project quality gates (`make verify-ai-tasks` and `make check`).

## Task Description

### Problem Statement

PyPost standalone servers allow collections of API tools and requests to be exposed directly to AI agents as MCP services. Currently, automated test coverage for standalone servers relies on internal in-memory state inspections and mock port allocations. In production, however, external clients connect via OS network sockets (HTTP/SSE loopback) or launch subprocesses using redirected standard input/output (`stdin`/`stdout`).

Physical transports introduce failure modes that in-memory unit tests cannot catch:
- TCP framing: Real TCP streams are stream-oriented bytes, not discrete messages. Large JSON payloads or fast message bursts split across multiple socket `recv` calls or combine multiple JSON-RPC messages into a single buffer read.
- OS stdio pipe buffering: OS pipes have limited buffer capacity (often 64KB). Writing large outputs to `stdout` while an agent is delayed in reading can block the server process indefinitely if buffering or async I/O is misconfigured.
- Concurrency and throughput bottlenecks: High-volume tool calls under rapid agent interactions can cause race conditions in connection handling, task dispatch, or response routing.
- Resource leaks: Improper socket shutdown or subprocess management leaves orphaned processes running in the background and lingering socket bindings, preventing server restarts on the same ports.

A comprehensive stress-testing suite executing real wire-level exchanges is required to guarantee production robustness.

### Scope

- **Real Loopback Socket Stress Testing**:
  - Live TCP socket / HTTP SSE connection establishment, handshake, request bursts, and teardown against standalone MCP server instances.
  - Stress testing with continuous request sequences, verifying response integrity and latency stability under sustained load.
- **Real Stdio IPC Stress Testing**:
  - Spawning standalone MCP server processes with connected OS pipes (`stdin`, `stdout`, `stderr`).
  - Transmitting JSON-RPC protocol messages across stdio pipes, validating framed parsing and bi-directional communication under sustained multi-message bursts.
- **Wire Framing and Boundary Fragmentation**:
  - Validating correct packet reassembly when JSON-RPC messages are segmented across arbitrary byte boundaries or combined in single read buffers.
  - Transmitting large payloads to test transport buffer handling without deadlocks or truncation.
- **Lifecycle Teardown & OS Resource Hygiene**:
  - Verifying deterministic process termination, pipe closure, thread cessation, and socket release upon session conclusion.
  - Validating that no orphan processes or unreleased socket bindings remain after test execution.

### Out of Scope

- Developing UI components, desktop dialogs, or graphical settings (this task focuses strictly on transport stress testing and protocol verification).
- Redesigning the collection catalog schema or variable resolution engine (established in prior tasks).
- Introducing third-party external cloud testing services or remote network dependencies (all tests run on local loopback/OS pipes).

### Functional Requirements

- **FR1 (Real Socket & Stdio IPC Communication)**: The test suite must establish real physical communication channels—specifically loopback TCP connections and OS stdio process pipes—transmitting actual JSON-RPC wire payloads between clients and standalone servers without mock transports.
- **FR2 (Protocol Lifecycle Sequence Validation)**: Standalone servers must complete the full protocol negotiation lifecycle over live wire channels:
  1. Initialization handshake (negotiating protocol version and capabilities).
  2. Tool discovery (listing registered collection tools with schema definitions).
  3. Tool execution (invoking tools with parameters and receiving structured results).
  4. Disconnection (closing sessions cleanly with proper protocol termination).
- **FR3 (Wire Framing & Message Integrity)**: The system must accurately frame and parse messages regardless of network packet boundaries:
  - Multi-message bursts arriving in a single read buffer must all be parsed and responded to in sequence.
  - Fragmented packets split across arbitrary byte boundaries must be buffered and reconstructed without JSON syntax errors.
  - Large message payloads exceeding operating system default buffer sizes (e.g. 64KB+) must transmit and complete without truncation or deadlock.
- **FR4 (Sustained Throughput & Concurrency Under Load)**: The server must withstand sustained load without failure:
  - Handle concurrent or continuous streams of tool execution requests without dropping connections or corrupting response mappings.
  - Maintain consistent response delivery without indefinite socket stalls or memory leaks during the stress burst.
- **FR5 (Deterministic Lifecycle Teardown & Cleanup)**: Server shutdown must guarantee complete resource reclamation:
  - Loopback TCP sockets must close immediately without lingering hung bindings.
  - Stdio subprocesses must terminate promptly without leaving orphaned background processes.
  - Internal server threads must shut down cleanly within bounded timeouts.

### Non-Functional Requirements

- **NFR1 (Test Reliability & Flakiness Prevention)**: All stress tests must be 100% deterministic, avoiding arbitrary fixed sleeps; synchronization must rely on bounded polling or explicit event readiness gates.
- **NFR2 (Bounded Execution Time)**: Stress test scenarios must execute efficiently within bounded timeouts conforming to the project's testing contracts (`@pytest.mark.timeout(30)` or equivalent per test node), avoiding CI job degradation.
- **NFR3 (Port and Resource Isolation)**: Dynamic port allocation must prevent collisions between concurrent test runs, and test fixtures must guarantee clean teardown even if test assertions fail.
- **NFR4 (Resource Conservation)**: Stress testing must operate within conservative CPU and memory budgets suitable for constrained CI worker environments.

### Main Business Entities

| Business Entity | Description | Attributes (Business Perspective) |
| --- | --- | --- |
| **Standalone MCP Server** | Self-contained tool execution service exposing collection operations over real OS communication channels. | Server identifier, transport mode (TCP loopback, stdio), bound address/port, process identifier, operational state. |
| **Transport Channel** | Physical operating system communication medium connecting an external client to the server. | Channel type (Loopback TCP Socket, OS Stdio Pipe), buffer capacity, connection status. |
| **JSON-RPC Wire Frame** | Serialized protocol message transmitted across the transport channel. | Protocol version, message identifier, method (initialize, tools/list, tools/call), payload size, raw framing boundaries. |
| **Protocol Session** | Single end-to-end conversation between a client and a server over a transport channel. | Session state (uninitialized, initialized, active, terminating, closed), negotiated capabilities, active requests count. |
| **Stress Load Profile** | Specification of volume, concurrency, and payload characteristics applied during verification. | Message count, burst rate, payload size category (small, medium, large/chunked), concurrency level, timeout limit. |
| **Resource Reclamation Contract** | Verification criteria ensuring complete cleanup of OS handles following session termination. | Process exit status, socket port availability, open descriptor count, thread count. |

### User Scenarios

#### Scenario 1: Live TCP Loopback Protocol Lifecycle & Tool Execution
An external client connects to a standalone server via a loopback TCP socket. The client sends a protocol initialization request. The server replies with supported capabilities. The client requests the list of exposed collection tools, receives the schema, and calls a tool with required parameters. The server processes the request and returns the structured result over the socket. The client disconnects, and the server closes the connection cleanly.

#### Scenario 2: Packet Fragmentation and Multi-Message Bursts
A client generates rapid bursts of requests, transmitting fragmented TCP chunks where single JSON-RPC messages are split across partial socket sends, or multiple requests are concatenated into a single packet. The standalone server reconstructs the fragmented frames, processes each request, and returns valid responses for all messages without dropping requests or raising framing parse errors.

#### Scenario 3: Stdio Subprocess Pipeline Stress
A client launches the standalone server as a subprocess communicating via `stdin` and `stdout`. The client floods the pipe with continuous tool execution calls with large payloads (exceeding pipe buffer limits). The server reads the input, executes the calls, and writes responses without blocking on pipe buffers or deadlocking. Upon completion, the client closes `stdin`, and the server process exits cleanly with a success code.

#### Scenario 4: Clean Shutdown and Rapid Port Re-binding
A standalone server running on a specific loopback port is subjected to a load burst and then signaled to terminate. The server stops accepting new connections, drains pending work, terminates all worker threads, and releases the TCP port. Immediately afterward, a new server instance binds to the exact same port without encountering port-in-use (`EADDRINUSE`) errors.

## Q&A

**Q: Why are real socket and stdio IPC stress tests necessary when in-process unit and integration tests already pass?**  
A: In-process tests call Python methods directly inside the same memory space, completely bypassing OS networking stacks, socket buffers, serialization framing, and subprocess pipe I/O. In production, AI clients connect via real loopback network sockets or stdio pipes. Only live wire tests can detect packet fragmentation bugs, pipe buffer deadlocks, socket lifecycle leaks, and transport-level race conditions.

**Q: What transport modes must be covered?**  
A: Both primary MCP communication transports used by standalone servers:
1. Real loopback TCP sockets (HTTP/SSE transport).
2. Operating system stdio pipes (`stdin`/`stdout`/`stderr` subprocess communication).

**Q: Does this task require modifying existing application production code?**  
A: The primary goal is delivering the comprehensive wire-level stress test suite and harness. However, if live wire stress testing exposes real framing bugs, buffer deadlocks, or socket descriptor leaks in standalone server handling, targeted production fixes will be implemented to ensure the servers meet the reliability contracts.

**Q: How does this test suite avoid hanging or failing in CI environments?**  
A: Tests will strictly comply with project testing contracts: bounded timeouts (`@pytest.mark.timeout(30)`), dynamic ephemeral port selection, bounded polling loops instead of fixed sleeps, and robust `try ... finally` or context manager resource cleanup to guarantee no leaked processes or ports remain regardless of test outcome.
