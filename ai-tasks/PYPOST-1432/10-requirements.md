# PYPOST-1432: Zero-Copy Memory Optimization for RawTcpWireClient

## Goals

In PyPost, high-throughput integration testing, fuzzing stress runs, and wire-level protocol validation rely heavily on `RawTcpWireClient` to simulate physical TCP transport behavior. The client inspects raw HTTP/1.1 and Model Context Protocol (MCP) transport streams, parses incoming status lines and headers, and consumes payload chunks and body segments.

Currently, as stream data arrives across network reads, `RawTcpWireClient` buffers unread bytes in a linear buffer and repeatedly slices it to partition headers, extract individual chunk payloads, and preserve leftover unconsumed bytes for subsequent responses. In high-volume test scenarios—such as multi-megabyte payload transfers, continuous chunked streaming, pipelined requests, and aggressive burst fuzzing—these repetitive slicing operations perform quadratic memory copying. Each slice duplicates memory in the Python runtime, triggering excessive allocations, intense garbage collection (GC) pressure, memory spikes, and latency jitter in test harnesses.

The primary business goal of this task is to eliminate unnecessary memory copying and buffer allocation churn in `RawTcpWireClient`. By transitioning buffer consumption from repetitive byte array slicing to a zero-copy windowing strategy, test suites and stress harnesses can process large bursts and high-frequency chunked streams with minimal memory overhead, predictable runtime execution, and significantly increased test harness throughput.

## Programming Language

- **Implementation language**: Python

## User Stories

- As a **test harness and integration suite developer**, I want `RawTcpWireClient` to parse large burst responses and high-frequency chunked payloads without allocating repetitive intermediate memory buffers, so that stress test suites run with predictable latency and minimal resource overhead.
- As a **QA engineer running fuzzing and negative test suites**, I want the wire client to handle continuous streams and fragmented transmissions without memory bloat or GC slowdowns, so that sustained fuzzing campaigns can run stably for long durations on resource-constrained CI runners.
- As a **CI/CD pipeline operator**, I want protocol tests involving large data transfers (multi-megabyte payloads, hundreds of pipelined responses) to execute rapidly and predictably, so that test jobs do not experience transient timeout flakiness caused by garbage collection pauses.
- As a **protocol test author**, I want the public interface and return data semantics of `RawTcpWireClient.read_http_response()` to remain completely identical and backward compatible, so that all existing tests and JSON-RPC decoders continue working seamlessly without requiring code modifications.
- As a **PyPost framework maintainer**, I want buffer consumption logic in the test harness to be robust, clean, and leak-free, ensuring active buffers are properly released or compacted when unread data is exhausted.

## Definition of Done

This task is considered complete when:
1. Repetitive buffer copying during header parsing, chunked payload extraction, and Content-Length body consumption is replaced with zero-copy buffer slicing and windowing.
2. `RawTcpWireClient` maintains complete functional correctness for all supported HTTP/1.1 response patterns:
   - Status line and header parsing, including delimiter detection across chunk boundaries.
   - Session identification header capture (`mcp-session-id`).
   - Transfer-Encoding: chunked response parsing, including multi-chunk reassembly and terminating chunk handling.
   - Content-Length delimited payload consumption.
   - Residual byte preservation across pipelined responses and subsequent reads.
3. The public interface and return signature of `RawTcpWireClient` (`read_http_response() -> tuple[int, dict[str, str], bytes]`) remain strictly preserved with identical return types.
4. Memory allocation churn and copying operations during chunked parsing and residual stream handling are substantially reduced in high-volume burst scenarios.
5. Buffer state is properly managed without memory leaks, ensuring that underlying memory from fully consumed buffers is released and unread residual data is accurately tracked.
6. All existing wire client unit tests, negative fuzzing tests, and MCP transport test suites pass green without regressions.
7. The repository quality gate passes (`make check` and `make verify-ai-tasks`).

## Task Description

### Problem Statement

`RawTcpWireClient` is designed to provide low-level socket stream injection and response verification for HTTP/1.1 and MCP streamable transports. When reading responses:
1. Incoming socket chunks are appended to an internal buffer until the header delimiter (`\r\n\r\n`) is encountered.
2. The buffer is partitioned into header and body segments.
3. If the response utilizes chunked transfer encoding, the client repeatedly inspects chunk length hexadecimal delimiters, extracts chunk payloads, and slices the remainder of the buffer.
4. If a response is pipelined or contains extra bytes beyond the current message boundary, the remaining unconsumed data is retained in the buffer for the next read operation.

Under the current implementation, every slicing operation creates a new byte buffer copy. When processing large responses with hundreds or thousands of chunked fragments, or multi-megabyte data streams, this leads to $O(N^2)$ data duplication. On CI runners and stress test environments, this produces high memory churn, increased garbage collection frequency, and sporadic timeout failures in timing-sensitive wire tests.

### Scope

- **In-Scope**:
  - Buffer management and stream consumption within `RawTcpWireClient` during reading of HTTP responses, headers, chunked payloads, and Content-Length bodies.
  - Zero-copy windowing / slicing mechanisms across buffered socket data.
  - Safe buffer compaction or reset lifecycle when data has been fully consumed or when memory recycling is needed.
  - Comprehensive unit testing and performance verification of buffer efficiency under burst and fragmented workloads.

- **Out-of-Scope**:
  - Changes to standalone MCP servers or server-side response generators.
  - Modifications to higher-level JSON-RPC parser functions (`parse_jsonrpc_from_response`).
  - Modifications to socket connection lifecycle (`connect()`, `close()`) or outgoing transmission methods (`send_fragmented()`, `send_all()`).
  - Introduction of external third-party dependencies or C-based native extensions.

### Domain Entities and Conceptual Model

- **Wire Stream Buffer**: The internal memory buffer in `RawTcpWireClient` holding incoming byte data received from the network socket.
- **Buffer Window / View**: A non-copying window or slice positioned over the active, unconsumed byte region of the wire stream buffer.
- **Message Framing Delimiter**: Structural byte sequences (`\r\n\r\n`, `\r\n`, chunk size hex strings) identifying boundaries between HTTP headers, chunk metadata, payload data, and trailing fragments.
- **Payload Segment**: The extracted body data (either Content-Length bounded or reassembled from chunked transfer segments) representing the complete response payload.
- **Residual Stream Data**: Bytes already received from the socket that belong to subsequent pipelined HTTP responses or future network reads.
- **Buffer Compaction Lifecycle**: The operational policy that resets or compacts the internal buffer when all active data has been consumed or when residual data is shifted, avoiding unbounded memory retention.

### User Scenarios and Use Cases

#### Scenario 1: Multi-Chunked Payload Parsing Under Sustained Stream
- **Context**: A test executes a streaming MCP tool call where the server returns data encoded with `Transfer-Encoding: chunked` spanning multiple sequential chunks.
- **Action**: `RawTcpWireClient.read_http_response()` is invoked to consume the stream.
- **Expected Outcome**: Chunk length headers and chunk contents are sliced and parsed without copying the entire remaining buffer at each iteration. The final decoded payload matches the exact byte sequence transmitted, and intermediate memory churn is minimized.

#### Scenario 2: Large Burst Content-Length Response
- **Context**: An integration test receives a multi-megabyte MCP response with a defined `Content-Length`.
- **Action**: The client reads from the socket until the required length is satisfied.
- **Expected Outcome**: The response body is extracted efficiently without extraneous intermediate buffer reallocations, and any trailing bytes from a subsequent pipelined message remain intact in the buffer.

#### Scenario 3: Pipelined Multiple HTTP Responses
- **Context**: A client sends multiple pipelined requests and invokes `read_http_response()` iteratively.
- **Action**: The first call consumes only the first message; remaining bytes in the buffer are preserved for the second call.
- **Expected Outcome**: The active buffer window correctly points to the start of the next response without data corruption, truncation, or memory leakage.

#### Scenario 4: Partial and Fragmented Socket Reads
- **Context**: Network packets arrive in small, fragmented bursts where delimiters or chunk sizes are split across multiple `socket.recv()` calls.
- **Action**: The client iteratively reads more socket data to satisfy framing requirements.
- **Expected Outcome**: Incoming data extends the buffer cleanly, and windowing continues without losing state or skipping delimiters.

#### Scenario 5: Buffer Depletion and Reset
- **Context**: All responses have been fully read and processed, leaving zero unread bytes.
- **Action**: Subsequent read or client teardown occurs.
- **Expected Outcome**: The buffer state is cleanly reset or compacted, ensuring that no dangling references prevent garbage collection of old data buffers.

## Non-Functional Requirements

- **Performance & Allocation Efficiency**:
  - Eliminate quadratic buffer copying during iterative chunk decoding and stream slicing.
  - Slicing and advancing through buffer windows should operate in $O(1)$ allocation complexity per slice.
- **Reliability & Data Integrity**:
  - 100% byte fidelity: decoded payloads, status codes, headers, and residual buffers must match previous behavior exactly.
  - Robust exception handling when connections close prematurely or encounter malformed framing.
- **Maintainability & Clean Architecture**:
  - Well-documented internal buffer state and window lifecycle.
  - Standard Python idioms compatible with Python 3.10+.
- **Zero Regressions & Backward Compatibility**:
  - Public method signatures, return types (`tuple[int, dict[str, str], bytes]`), and class properties must remain unchanged.

## Constraints and Assumptions

- **Constraints**:
  - Python Standard Library Only: No third-party dependencies may be added.
  - Tooling Standard: All verification and testing operations must be executed exclusively via `make` targets (`make check`, `make test`, `make lint`, `make typecheck`, `make verify-ai-tasks`).
  - Read-Only Test Interfaces: Existing callers in `tests/test_mcp_standalone_wire_ipc_repro.py`, `tests/test_mcp_standalone_wire_ipv6.py`, `tests/test_mcp_wire_fuzzing_negative.py`, and `tests/test_raw_tcp_client_helper.py` must not require code modifications.
- **Assumptions**:
  - Sockets are non-blocking or configured with timeouts as specified during client initialization.
  - Residual data retained in the buffer between pipelined requests is within typical test message sizes.

## Q&A

- **Q: Why is zero-copy optimization necessary for a test helper class?**
  - **A**: `RawTcpWireClient` is not just a simple unit test helper; it acts as the primary wire-level client harness for high-concurrency IPC stress tests, fuzzing suites, and heavy burst scenarios. Memory churn and GC stalls during burst runs cause false-positive test timeouts, high CI worker resource usage, and non-deterministic test failures.
- **Q: Will switching to zero-copy slicing change the return type of `read_http_response()`?**
  - **A**: No. The return type remains `tuple[int, dict[str, str], bytes]`. Slicing optimization is internal to buffer traversal and chunk assembly. Callers expecting standard `bytes` will continue receiving immutable `bytes` objects.
- **Q: How will the client manage memory if a view holds an underlying buffer reference?**
  - **A**: Buffer management will include appropriate window offset tracking and periodic compaction or reset when data is consumed, ensuring that unused memory is released and not indefinitely retained.
- **Q: Are binary or text protocols affected?**
  - **A**: `RawTcpWireClient` operates on raw bytes at the wire layer for HTTP/1.1 transport. Header decoding and body extraction preserve raw byte content without altering character encodings or binary payloads.
