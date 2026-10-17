# PYPOST-1430: Implement Malformed JSON-RPC and Wire Framing Fuzzing Suite

## Goals

PyPost standalone Model Context Protocol (MCP) servers and embedded transport endpoints expose API collections and tools to external AI agents, IDEs, and client tools. In real-world environments, these clients communicate with PyPost servers across physical network channels (such as loopback TCP sockets carrying HTTP/SSE protocols).

Previous testing efforts (such as [PYPOST-1416](file:///home/src/ai-tasks/PYPOST-1416/10-requirements.md) and [PYPOST-1428](file:///home/src/ai-tasks/PYPOST-1428/10-requirements.md)) established positive stress-testing suites verifying that standalone servers correctly reassemble fragmented packets, manage multi-message bursts, and handle large payloads when all frames conform to valid protocol and framing rules.

However, real-world networks, buggy client libraries, network proxies, interrupted client connections, and misbehaving or compromised AI agents routinely produce malformed input. These anomalies include:
1. Truncated JSON messages and incomplete transmission buffers cut off mid-payload.
2. Syntactically invalid or split JSON tokens and mismatched structural delimiters.
3. Invalid JSON-RPC envelopes (e.g. non-object root payloads, invalid protocol versions, missing methods, or illegal identifier types).
4. Malformed HTTP headers and framing violations (e.g. corrupted `Content-Length` headers, invalid chunk hex sizes, malformed chunk trailers, or missing header terminators).
5. Non-UTF-8 byte sequences and raw binary noise injected directly into protocol sockets.

Without systematic negative fuzzing verification, protocol parsers and wire connection handlers risk catastrophic failure modes: crashing the server process, raising unhandled worker exceptions, hanging socket reading threads indefinitely, exhausting file descriptors, or leaving the server in an unrecoverable corrupted state that blocks subsequent legitimate agent interactions.

The business goal of this task is to implement a comprehensive negative fuzzing and resilience test suite. This suite exercises MCP wire transports and protocol parsers against malformed framing, corrupted/split packets, invalid JSON-RPC payloads, and HTTP protocol violations, guaranteeing that PyPost MCP servers remain rock-solid, reject invalid input gracefully without process crashes or hung socket handlers, promptly reclaim resources, and continue serving valid requests.

**Implementation language**: Python

## User Stories

- As an **AI Agent / Client Integrator**, I want the MCP server to reject malformed or truncated JSON-RPC payloads with deterministic protocol-level error responses (or standard HTTP client error statuses) rather than hanging silently or dropping the socket without explanation, so that client applications can cleanly detect transport/protocol failures and recover.
- As an **API Developer / Application User**, I want malformed wire requests or corrupted network frames from external clients not to crash the PyPost host application or terminate standalone server processes, so that other active tools, collections, and background workflows remain fully operational.
- As a **DevOps / Platform Operator**, I want socket handlers receiving malformed HTTP framing or invalid chunk headers to terminate or reset connections promptly without hanging connection threads or leaking open socket descriptors, so that system resources remain bounded and ports stay available.
- As a **QA / Maintainer**, I want an automated fuzzing and negative test suite under `make test` that locks parser resilience contracts, so that future parser optimizations, refactoring, or transport upgrades cannot introduce regressions that crash servers or hang on malformed inputs.

## Definition of Done

This task is considered complete when:
1. An automated negative fuzzing and resilience test suite is added under `tests/` that exercises standalone MCP servers over physical loopback TCP wire connections without in-memory mocks.
2. The fuzzing suite covers negative scenarios across wire framing and protocol layers:
   - **Truncated JSON Payloads**: Streams cut off mid-key, mid-string, mid-number, or with unclosed object/array brackets.
   - **Split & Corrupted JSON Tokens**: Unescaped control characters, malformed unicode escapes, invalid primitive literals, and split token sequences.
   - **Invalid JSON-RPC Envelopes**: Non-object root values (arrays, primitives), unsupported or missing `jsonrpc` protocol version attributes, missing method names on requests, and invalid `id` value types.
   - **Malformed HTTP Wire Framing**: Corrupted `Content-Length` values (negative, non-numeric, mismatched lengths), invalid chunked transfer framing (corrupted hex chunk sizes, missing CRLF delimiters, premature EOF inside chunk data), and malformed or unterminated HTTP request headers.
   - **Illegal Byte Sequences**: Non-UTF-8 byte streams and arbitrary binary noise transmitted directly over the raw wire socket.
3. Server resilience contracts are strictly verified:
   - The server process and background worker threads never crash or terminate unexpectedly when bombarded with malformed inputs.
   - Socket connection handlers never hang indefinitely; incomplete frames or broken chunk streams trigger bounded timeout resets or clean connection closure.
   - The server returns standardized protocol error responses (e.g. JSON-RPC Parse error `-32700`, Invalid Request `-32600`, or HTTP `400 Bad Request` / `422 Unprocessable Entity`) where the protocol framing allows an HTTP-level response, or cleanly closes the socket when the HTTP framing itself is unparseable.
   - Subsequent valid MCP protocol requests (such as `initialize` and `tools/list`) sent immediately after malformed payloads on a fresh connection (or over a recovered connection) succeed completely, verifying that parser error states do not contaminate future requests.
   - All connection sockets and descriptors are deterministically reclaimed without leaks.
4. Test suite conforms to repository testing standards:
   - Enforces bounded test timeouts per project test rules (`@pytest.mark.timeout(30)` or equivalent).
   - Uses dynamic ephemeral port allocation and robust teardown fixtures to eliminate cross-test port conflicts.
   - Completely passes under `make test` and `make check`.
5. AI task artifacts integrity is verified via `make verify-ai-tasks`.

## Task Description

### Problem Statement

Stand-alone Model Context Protocol servers in PyPost process external client requests transmitted across physical loopback TCP connections using streamable HTTP and SSE wire protocols. The protocol stack operates across two interdependent parsing layers:
1. **HTTP Wire Framing Layer**: Parses HTTP request lines, headers, `Content-Length` framing, and chunked transfer encoding (`Transfer-Encoding: chunked`).
2. **JSON-RPC Protocol Layer**: Parses JSON character streams into structured message objects, validating the JSON-RPC 2.0 schema requirements (envelope structure, `jsonrpc` version string, `method`, `params`, and `id`).

While previous stress testing verified that valid messages are assembled correctly under packet fragmentation, negative inputs pose severe operational hazards:
- An unexpected EOF during a chunk payload or an invalid hexadecimal chunk size can cause naive socket readers to enter infinite retry loops or block worker threads indefinitely.
- Broken JSON tokens or unclosed brackets could raise unhandled parser exceptions that kill the server listener thread or child process.
- Corrupted `Content-Length` headers could cause buffer over-reads or unhandled parsing exceptions.
- Non-UTF-8 binary noise could cause uncaught decoding errors that crash server connection workers.

To guarantee high availability and operational safety, PyPost requires a dedicated fuzzing and negative test suite that continuously verifies the server's resilience against these real-world wire faults.

### Scope

- **In Scope**:
  - Live loopback TCP socket fuzzing scenarios exercising standalone MCP servers with raw socket transmissions.
  - Test scenarios for truncated JSON, invalid JSON tokens, and illegal JSON-RPC envelopes.
  - Test scenarios for corrupted HTTP headers, invalid `Content-Length`, and malformed chunked transfer framing.
  - Test scenarios for non-UTF-8 byte sequences and binary garbage payloads.
  - Verification of non-crash guarantees, bounded socket teardown, standardized error responses, and clean post-fault recovery for subsequent requests.
  - Production bug fixes if and only if fuzzing exposes unhandled crashes or hangs in existing server handling.

- **Out of Scope**:
  - In-process GUI presentation components or desktop dialog visual formatting.
  - IPv6 transport coverage (separately tracked in [PYPOST-1431](https://pypost.atlassian.net/browse/PYPOST-1431)).
  - Internal buffer optimization for test helpers (separately tracked in [PYPOST-1432](https://pypost.atlassian.net/browse/PYPOST-1432)).
  - Modifying the underlying collection execution engine or tool business logic.

### Functional Requirements

- **FR1 (Wire Framing Malformation Resilience)**: The standalone MCP server wire listener must handle corrupted HTTP framing—including truncated headers, non-numeric `Content-Length`, invalid chunk size hex strings, and incomplete chunk payloads—without crashing, deadlocking, or blocking the listener thread.
- **FR2 (JSON Parsing Robustness)**: The MCP message parser must intercept malformed JSON data (truncated syntax, invalid escape sequences, split tokens) and return a standard JSON-RPC Parse Error (`-32700`) or close the socket cleanly without throwing unhandled exceptions to the process level.
- **FR3 (JSON-RPC Schema Validation)**: The server must validate JSON-RPC 2.0 message contracts (root object structure, version string `"2.0"`, presence of `method` for requests, appropriate `id` types) and return standard Invalid Request (`-32600`) or Invalid Params (`-32602`) errors when violated.
- **FR4 (Non-UTF-8 and Binary Garbage Handling)**: When receiving arbitrary non-UTF-8 bytes or corrupted binary noise over raw TCP wire, the server must reject the data and close or reset the socket cleanly without unhandled character decoding crashes.
- **FR5 (Post-Fault Operational Continuity)**: Processing malformed frames must never leave the server in a broken or locked state; immediately following any malformed request, valid MCP protocol operations (e.g. `initialize`, `tools/list`, `tools/call`) on a new connection must execute successfully.
- **FR6 (Deterministic Socket & Thread Teardown)**: Malformed or interrupted connections must be closed within bounded timeouts, and all associated socket handles, buffers, and worker threads must be released without resource leaks.

### Non-Functional Requirements

- **NFR1 (Fault Isolation & Stability)**: The standalone MCP server process and host application must maintain 100% uptime when subjected to continuous streams of invalid or corrupted wire frames.
- **NFR2 (Deterministic Execution & Bounded Timeouts)**: All fuzzing test cases must operate with bounded socket read/write timeouts and explicit synchronization gates. No test case may rely on arbitrary sleeps or risk hanging CI runners.
- **NFR3 (Port Isolation & Cleanup)**: All test cases must use dynamically allocated ephemeral ports and guaranteed cleanup fixtures to ensure zero cross-test interference or lingering port bindings.
- **NFR4 (Performance & CI Budget)**: The fuzzing test suite must execute rapidly and efficiently within standard CI job timeout limits without excessive CPU or memory consumption.

### Main Business Entities

| Business Entity | Description | Attributes (Business Perspective) |
| --- | --- | --- |
| **Standalone MCP Server** | Standalone tool server process exposing API collections to AI clients over network transports. | Server state (running, stopped), host, port, active connections, thread pool health. |
| **Raw TCP Wire Connection** | Physical operating system socket channel over which bytes are transmitted to and from the server. | Socket handle, local/remote address, connection state (connected, closed, reset). |
| **Malformed Wire Frame** | A byte sequence sent over the wire that violates HTTP specification or chunked framing rules. | Framing anomaly type (truncated headers, corrupted length, invalid chunk hex, incomplete chunk body), payload length. |
| **Malformed Protocol Payload** | A message payload that violates JSON syntax or JSON-RPC 2.0 schema specifications. | Malformation category (truncated JSON, invalid token, non-object root, wrong version, missing method, bad id), raw bytes. |
| **Protocol Error Response** | Standardized error message returned to the client indicating the nature of the rejection. | Error code (HTTP 400/422, JSON-RPC -32700 Parse Error, -32600 Invalid Request), error message, correlation ID. |
| **Resilience Contract** | Operational guarantee that the server survives input anomalies, reclaims resources, and remains available. | Server process alive, socket cleanly closed/replied, zero hung threads, successful subsequent valid handshake. |

### User Scenarios

#### Scenario 1: Truncated JSON Payload on Raw Wire
An external client connects over a TCP socket, sends valid HTTP request headers, and begins transmitting a JSON-RPC request body. Midway through a parameter key or value, the client terminates transmission or closes the connection prematurely. The server parser detects the incomplete payload, avoids blocking indefinitely, and terminates the connection cleanly without raising an unhandled exception or leaving the worker thread hung.

#### Scenario 2: Corrupted Chunked Framing & Invalid Hex Sizes
A client transmits a request using chunked transfer encoding (`Transfer-Encoding: chunked`). The client sends an invalid non-hexadecimal chunk length indicator (e.g. `ZZ\r\n`) or specifies a chunk size larger than the actual bytes delivered before EOF. The server wire transport detects the framing violation, terminates the connection or returns an HTTP client error, and immediately returns to listening for new connections.

#### Scenario 3: Non-UTF-8 Bytes and Binary Noise Injection
A misconfigured client or network scanner opens a TCP connection to the standalone server and writes a sequence of random binary bytes that do not represent valid UTF-8 characters. The server wire reader safely catches the decoding error, rejects the request, closes the socket, and maintains normal background operation.

#### Scenario 4: Post-Fault Service Continuity
Following a series of malformed HTTP requests, truncated JSON messages, and non-UTF-8 bursts, an AI agent opens a new connection to the server and initiates a standard MCP handshake (`initialize` followed by `tools/list`). The server responds immediately with valid capabilities and tool definitions, demonstrating that prior faults did not contaminate parser state, leak connection slots, or impair service availability.

## Q&A

**Q: Why is a dedicated negative fuzzing suite needed when PYPOST-1416 stress tests already exist?**  
A: PYPOST-1416 validated positive stress scenarios: high volume, large valid payloads, valid packet fragmentation (1-byte/7-byte slices), and concurrent requests where all messages complied with HTTP and JSON-RPC specifications. It did not test how the server reacts when framing rules or syntax rules are actively broken. In production, network anomalies and diverse client implementations frequently produce broken frames; without explicit negative testing, parser crashes and socket hangs remain undetected.

**Q: What layers are targeted by this fuzzing suite?**  
A: The suite targets two distinct layers across physical TCP connections:
1. The transport framing layer (HTTP request line, headers, `Content-Length`, and chunked transfer encoding).
2. The protocol parser layer (JSON syntax validation and JSON-RPC 2.0 contract validation).

**Q: What is the expected server behavior when receiving malformed inputs?**  
A: The server must satisfy two core requirements:
1. **Safety**: Never crash the process, never leak open sockets or threads, and never block indefinitely.
2. **Predictability**: Return a standardized error response (e.g. HTTP 400 Bad Request, or JSON-RPC -32700 / -32600 error) whenever the transport framing permits sending a response; if the wire framing itself is too corrupted to send an HTTP response (e.g. truncated headers or socket closed mid-chunk), the server must close the connection cleanly.

**Q: Will this task require modifications to production code?**  
A: The primary goal of this task is implementing the comprehensive negative test suite. However, if the fuzzing scenarios expose real bugs in existing server code—such as unhandled exceptions that terminate worker threads or infinite socket read loops—targeted production fixes will be implemented to satisfy the resilience contract.

**Q: How does this test suite maintain high reliability in CI?**  
A: Every test uses dynamic ephemeral port allocation, explicit per-test timeouts, non-blocking or bounded socket operations, and robust teardown fixtures to ensure no socket or process leaks occur regardless of test outcomes.
