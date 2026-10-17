# PYPOST-1431: Add IPv6 Socket Transport Coverage for Standalone MCP Servers

## Goals

PyPost standalone Model Context Protocol (MCP) servers expose API collections, request templates, and custom tools to external AI agents, developer IDEs, and automation clients over local network transports. These endpoints serve as critical integration bridges, executing requests and streaming responses using standard HTTP and JSON-RPC wire protocols.

In modern enterprise infrastructure, cloud container runtimes, Kubernetes clusters, and developer workstations, networking topologies are increasingly configured as dual-stack or IPv6-only. In environments where legacy IPv4 loopback (`127.0.0.1`) is deprioritized, restricted, or entirely absent, applications and AI agents rely exclusively on IPv6 loopback (`::1`) for inter-process communication (IPC) and local socket transport.

Currently, PyPost standalone MCP server test suites, client harnesses, and wire verification utilities exclusively target IPv4 loopback (`127.0.0.1`). This gap leaves IPv6 transport pathways (`::1`, `[::1]`, and `AF_INET6`) completely unexercised in the continuous integration test suite.

Without automated test coverage for IPv6 wire transport, changes to socket binding routines, HTTP request framing (such as bracketed host header formatting), address resolution, or transport lifecycles risk introducing severe latent regressions:
1. **Socket Family Mismatches**: Connect errors, unhandled OS exceptions, or failure to resolve and bind to IPv6 loopback addresses.
2. **HTTP Framing Incompatibilities**: Malformed or unbracketed `Host` headers (e.g. `Host: ::1:port` instead of `Host: [::1]:port`) that violate HTTP/1.1 specifications and cause client or server-side parser rejections.
3. **Transport Hangs or Resource Leaks**: Incomplete connection handshakes, unhandled socket timeouts, or failed teardown during server shutdown under IPv6.
4. **Integration Blind Spots**: Inability to verify that clients utilizing the shared `RawTcpWireClient` test harness can communicate with MCP servers across IPv6 networks.

The business goal of this task is to extend the `RawTcpWireClient` test helper to support IPv6 address resolution, socket connection, and HTTP framing, and to add a comprehensive integration test suite validating standalone MCP server port binding, lifecycle transitions, protocol handshakes, tool invocation, and connection teardown across IPv6 loopback (`::1`).

**Implementation language**: Python

## User Stories

- As an **AI Agent / Client Integrator operating in an IPv6 environment**, I want to connect to standalone MCP servers over IPv6 loopback (`::1`), perform full protocol handshakes, and execute tools, so that my workflows function seamlessly on modern dual-stack or IPv6-only hosts.
- As an **Application Developer**, I want standalone MCP server lifecycle management to reliably bind, listen, and shut down on IPv6 endpoints without socket conflicts or process hangs, so that tool services integrate cleanly with local tooling and containers.
- As a **QA / Test Engineer**, I want the repository's shared raw TCP wire test client (`RawTcpWireClient`) to seamlessly support IPv6 target addresses and bracketed host formatting, so that wire transport, fragmentation, and fuzzing tests can be executed against IPv6 endpoints.
- As a **DevOps / Platform Engineer**, I want automated CI tests validating IPv6 loopback transport fidelity with automatic environment detection, so that IPv6-related regressions are caught immediately without failing on legacy environments lacking IPv6 kernel support.

## Definition of Done

This task is considered complete when:
1. **Raw TCP Wire Client IPv6 Capability**:
   - `RawTcpWireClient` supports target hostnames and IP literals for both IPv4 and IPv6 (specifically `::1` and bracketed `[::1]`).
   - Sockets created by `RawTcpWireClient` dynamically select the correct address family (`socket.AF_INET6` for IPv6 targets).
   - HTTP/1.1 request formatting in `RawTcpWireClient` automatically formats the `Host` header using standard bracketed notation (e.g. `Host: [::1]:port`) when communicating over IPv6.
2. **IPv6 Standalone MCP Server Test Suite**:
   - An automated integration test suite under `tests/` verifies end-to-end communication with standalone MCP servers over IPv6 loopback (`::1`).
   - The test suite exercises:
     - Ephemeral port allocation and socket binding on IPv6 loopback.
     - Server startup, readiness polling, and listening status verification on IPv6.
     - MCP protocol initialization handshake (`initialize` request followed by `notifications/initialized`).
     - Tool discovery (`tools/list`) and tool execution (`tools/call`) over IPv6.
     - Wire framing verification (both `Content-Length` bounded responses and chunked transfer streams).
     - Graceful server shutdown and clean socket descriptor release on IPv6.
3. **Environment Detection & Test Resilience**:
   - The test suite includes detection of OS-level IPv6 loopback availability, ensuring tests pass or skip cleanly with informative messages if run on platforms or containers where IPv6 is not configured.
   - All tests enforce strict, bounded timeouts per repository testing standards (`pytestmark = pytest.mark.timeout(...)`).
4. **Quality Gates**:
   - Code complies with formatting, linting, and type checking requirements (`make lint`, `make typecheck`).
   - The entire fast test suite passes (`make test`).
   - AI task artifacts pass integrity validation (`make verify-ai-tasks`).
5. **Roadmap & Step Artifacts**:
   - `ai-tasks/PYPOST-1431/00-roadmap.md` is initialized and maintained throughout all workflow steps.

## Task Description

### Problem Statement

Model Context Protocol (MCP) servers in PyPost operate over standard streamable HTTP/SSE and raw socket transports. While the underlying application server implementation supports configurable host binding, existing integration test harnesses—specifically `RawTcpWireClient` and associated repro suites—hardcode IPv4 loopback (`127.0.0.1`) and `socket.AF_INET`.

Specifically:
- `RawTcpWireClient` unconditionally creates an `AF_INET` socket descriptor and does not accommodate IPv6 address families.
- Wire request builders format `Host: {self.host}:{self.port}`, which produces invalid HTTP/1.1 syntax when `self.host` is an unbracketed IPv6 literal (e.g. `Host: ::1:8080` instead of RFC 3986 / RFC 7230 compliant `Host: [::1]:8080`).
- No integration tests exist to verify that standalone MCP servers successfully bind to `::1`, listen for connections, parse incoming HTTP requests over IPv6, route JSON-RPC tool calls, and release socket descriptors upon termination.

This lack of test coverage leaves IPv6 support vulnerable to accidental breakage during refactoring of server bind helpers, socket management, or protocol handlers.

### Scope

- **In Scope**:
  - Extending `RawTcpWireClient` to dynamically resolve target address families (`AF_INET` vs `AF_INET6`) and properly bracket IPv6 host headers in HTTP requests.
  - Adding integration tests that instantiate standalone MCP servers bound to IPv6 loopback (`::1`), execute MCP handshakes and tool requests, and verify responses.
  - Verifying clean port allocation, binding, and teardown over IPv6 loopback.
  - Providing a clean fallback / skip mechanism for environments where IPv6 loopback is unavailable.
- **Out of Scope**:
  - Global or public IPv6 internet routing, NAT64, DNS64, or multi-homed network configuration.
  - TLS/SSL encryption or certificate validation on IPv6 sockets (handled in dedicated security suites).
  - Modifying tool execution business logic or collection runtime behavior unrelated to transport.
  - Modifying external MCP client libraries.

### Functional Requirements

- **FR1 (IPv6 Address Family Support in Test Harness)**: The `RawTcpWireClient` must inspect the target host or address family and create a `socket.AF_INET6` stream socket when connecting to IPv6 endpoints such as `::1` or `[::1]`.
- **FR2 (RFC-Compliant HTTP Host Header Formatting)**: When building HTTP requests targeting an IPv6 literal address, `RawTcpWireClient` must format the `Host` header with brackets (e.g. `Host: [::1]:<port>`) while preserving standard formatting for IPv4 addresses and domain names.
- **FR3 (Standalone Server IPv6 Binding and Listening)**: Standalone MCP servers must successfully bind to IPv6 loopback (`::1`), report listening status, and accept incoming TCP connections over IPv6.
- **FR4 (Full MCP Protocol Lifecycle over IPv6)**: The test suite must validate that standalone MCP servers process the full MCP lifecycle over IPv6:
  - Protocol initialization (`initialize` request with client capabilities and version negotiation).
  - Client initialization notification (`notifications/initialized`).
  - Tool discovery (`tools/list` returning registered tool schemas).
  - Tool invocation (`tools/call` executing requests and returning structured results).
- **FR5 (Wire Framing and Session Fidelity)**: The IPv6 transport path must correctly handle both fixed `Content-Length` request/response bodies and `Transfer-Encoding: chunked` event streams, correctly associating requests with active `mcp-session-id` headers.
- **FR6 (Clean Teardown and Port Release)**: Stopping an IPv6 standalone MCP server must immediately terminate listening sockets and release OS port bindings, allowing immediate re-binding on the same host and port.
- **FR7 (Environment-Aware Execution)**: Test fixtures and runners must detect whether the runtime environment supports IPv6 socket binding; if IPv6 loopback is not available, tests must skip cleanly without generating false-positive test failures.

### Non-Functional Requirements

- **NFR1 (Deterministic Execution & Bounded Timeouts)**: All IPv6 socket operations, connection polls, and server lifecycle transitions must execute within deterministic, bounded timeouts (under 30 seconds), preventing CI pipeline deadlocks.
- **NFR2 (Port Isolation)**: Dynamic port allocation must be used for IPv6 test runs to eliminate port contention or collisions during parallel test execution.
- **NFR3 (Parity and Consistency)**: Server responses, protocol behaviors, and error handling over IPv6 must exhibit complete behavioral parity with IPv4 loopback operations.
- **NFR4 (Resource Reclaim)**: Tests must guarantee deterministic socket closure and resource reclamation via context managers or explicit teardown fixtures.

### Main Business Entities

| Business Entity | Description | Attributes (Business Perspective) |
| --- | --- | --- |
| **Standalone MCP Server** | Local tool server process exposing API collections to AI clients via socket transport. | Server ID, host binding (`127.0.0.1` or `::1`), bound port, running state (`stopped`, `listening`, `failed`). |
| **IPv6 Loopback Endpoint** | Standard local IPv6 networking interface (`::1`) used for local machine IPC. | Address literal (`::1`), bracketed representation (`[::1]`), address family (`AF_INET6`), target port. |
| **Raw TCP Wire Client** | Low-level test harness injecting raw socket bytes and validating HTTP/JSON-RPC framing. | Target host, target port, address family, socket handle, session ID, read/write timeout. |
| **HTTP Wire Frame** | Physical byte sequence sent over the socket representing HTTP/1.1 request/response. | Request line, `Host` header (bracketed for IPv6), `Content-Length` / `Transfer-Encoding`, payload body. |
| **MCP Protocol Session** | State of active Model Context Protocol communication between client and server. | Session ID, protocol version, client capabilities, server capabilities, registered tools. |
| **Port Allocator** | Test utility that dynamically reserves available TCP ports on the target interface. | Target address family, candidate port range, lock file, bound status. |

### User Scenarios

#### Scenario 1: Standalone Server Initialization over IPv6
A test case starts a standalone MCP server configured with host `::1` and an dynamically allocated port. The server successfully binds to the IPv6 address and signals readiness. The raw TCP client connects to `[::1]:<port>` over an `AF_INET6` socket, sends an `initialize` JSON-RPC POST request with a bracketed `Host` header, and receives a 200 OK response containing the server's protocol version and capabilities.

#### Scenario 2: Tool Execution over IPv6 Loopback
Following initialization, the client sends a `tools/call` JSON-RPC request over the existing or a new IPv6 TCP connection to invoke an exposed API tool. The server executes the underlying request template, captures the result, and returns the formatted JSON-RPC result over the IPv6 socket with correct HTTP headers.

#### Scenario 3: Clean Server Teardown and Re-Binding
After completing test operations, the test harness triggers server shutdown. The server terminates its listener, closes background worker tasks, and releases the IPv6 socket descriptor. A subsequent socket bind attempt on `(::1, port)` immediately succeeds, confirming zero resource leaks or lingering socket holds.

#### Scenario 4: Test Execution on Platform Lacking IPv6 Support
In an execution environment (such as certain restricted container runners or legacy CI nodes) where IPv6 networking is disabled, the test suite attempts an ephemeral probe. Upon detecting that `socket.AF_INET6` binding raises `EAFNOSUPPORT` or `EADDRNOTAVAIL`, the test suite logs a clear message and cleanly skips the IPv6 test cases without reporting a build failure.

## Q&A

**Q: Why is dedicated IPv6 socket transport testing necessary when IPv4 is already covered?**  
A: Modern containerized and cloud platforms (such as Kubernetes and enterprise Linux distros) frequently operate in dual-stack or IPv6-only modes where IPv4 loopback is disabled or not mapped. Without automated IPv6 tests, socket family errors, host string parsing bugs, and bracketed header issues can completely disable MCP tool integration for users on IPv6 networks.

**Q: What changes are required in `RawTcpWireClient` to support IPv6?**  
A: `RawTcpWireClient` currently hardcodes `socket.AF_INET` and formats `Host: {self.host}:{self.port}`. To support IPv6, it must determine whether `host` is an IPv6 address (or accept an address family parameter), instantiate `socket.AF_INET6`, and ensure the HTTP `Host` header wraps IPv6 literals in brackets per RFC 3986 / RFC 7230 (e.g. `Host: [::1]:8080`).

**Q: Does this task require changes to production server code?**  
A: PyPost's server binding layer (`server_bind.py`) already contains `detect_address_family` and IPv6-aware logic. This task focuses on extending the test utilities (`RawTcpWireClient`) and adding comprehensive test coverage for standalone MCP servers over IPv6. If integration testing reveals edge cases in production server handling (such as socket option handling or host parsing in `MCPServerManager`), targeted fixes will be implemented.

**Q: How will test flakiness and port collisions be prevented?**  
A: Test suites will use dynamic ephemeral port allocation and safe teardown fixtures to ensure each test operates on an isolated, conflict-free port and cleanly frees resources upon completion.

**Q: How will tests behave in CI environments where IPv6 is disabled?**  
A: Tests will incorporate an environment check (e.g. attempting a transient probe bind on `::1`). If IPv6 loopback is not supported by the kernel or host environment, tests will skip gracefully using standard pytest skip mechanisms.
