# Standalone MCP Server Live Wire IPC & Stdio Transport Stress Testing

## Overview

In PyPost, Model Context Protocol (MCP) servers expose saved HTTP requests and collections as
discoverable, executable AI tools and resources. While in-process unit tests validate tool schema
registration and supplier dispatch mechanisms, they execute in memory and bypass the physical
operating system networking stack, socket buffers, kernel pipe buffers, and wire framing.

Story [PYPOST-1416](https://pypost.atlassian.net/browse/PYPOST-1416) established live wire IPC and
stdio transport stress testing in
[`test_mcp_standalone_wire_ipc_repro.py`](../../tests/test_mcp_standalone_wire_ipc_repro.py).
Story [PYPOST-1428](https://pypost.atlassian.net/browse/PYPOST-1428) extracted the reusable wire
client and response decoder into the shared test utility module
[`tests/helpers/raw_tcp_client.py`](file:///home/src/tests/helpers/raw_tcp_client.py)
for reuse across all MCP wire transport test suites. This document describes the architecture,
protocols, failure modes, shared test harness design, helper APIs, and execution guidelines for
validating standalone MCP server transports under physical wire and pipe conditions.

---

## Architecture & Transports

Standalone MCP servers in PyPost support two primary physical communication channels:
1. **Network Loopback TCP Sockets**: Streamable HTTP and Server-Sent Events (SSE) hosted on an ASGI
   Starlette application running on a background Uvicorn daemon thread managed by
   [`MCPServerManager`](file:///home/src/pypost/core/qt/mcp_server.py).
2. **Out-of-Process OS Pipes (Stdio)**: Child subprocesses communicating via standard input/output
   streams (`stdin`/`stdout`/`stderr`) using `mcp.server.stdio.stdio_server`.

```mermaid
flowchart TD
    subgraph ClientHarness["Test Harness / MCP Client"]
        WireClient["RawTcpWireClient (tests/helpers/raw_tcp_client.py)"]
        StdioHarness["Stdio Subprocess Runner"]
    end

    subgraph NetworkStack["OS Network Stack & Pipes"]
        Loopback["TCP Loopback (127.0.0.1:{port})"]
        Pipes["OS Kernel Pipes (stdin/stdout/stderr)"]
    end

    subgraph StandaloneServer["Standalone MCP Server Process"]
        Uvicorn["Uvicorn Background Worker"]
        Starlette["Starlette ASGI App"]
        StdioServer["mcp.server.stdio.stdio_server"]
        ServerImpl["MCPServerImpl (JSON-RPC 2.0)"]
    end

    WireClient -->|Raw TCP Frames| Loopback
    Loopback --> Uvicorn
    Uvicorn --> Starlette
    Starlette --> ServerImpl

    StdioHarness -->|PIPE_BUF / Non-blocking Drainers| Pipes
    Pipes --> StdioServer
    StdioServer --> ServerImpl
```

### 1. Streamable HTTP Wire Transport (`/mcp`)

- **Mount Point**: Mounted via `mcp.server.streamable_http_manager.StreamableHTTPSessionManager`.
- **Wire Framing**: Standard HTTP/1.1 `POST /mcp` requests.
- **Session Identification**: Session tracking occurs via the HTTP header `mcp-session-id: <uuid>`,
  assigned by the server on initial handshake.
- **Payload**: JSON-RPC 2.0 messages (requests, responses, notifications).
- **Keep-Alive**: Connections leverage HTTP/1.1 `Connection: keep-alive` to allow multiple
  pipelined or sequential requests over a single persistent TCP socket.

### 2. Legacy SSE Wire Transport (`/sse` & `/sse/messages`)

- **Mount Point**: Mounted via `mcp.server.sse.SseServerTransport`.
- **Stream Channel**: The client issues `GET /sse HTTP/1.1` with `Accept: text/event-stream`.
  The server keeps the HTTP connection open, returning `Content-Type: text/event-stream` and
  emitting an `endpoint` event containing the session URI:
  ```http
  event: endpoint
  data: /sse/messages?session_id=3fa85f64-5717-4562-b3fc-2c963f66afa6
  ```
- **Message Channel**: Client POSTs JSON-RPC requests to `/sse/messages?session_id=...`, which
  returns HTTP 202 Accepted. Responses are streamed back asynchronously over the active GET SSE
  connection as `event: message` blocks.

### 3. Out-of-Process Stdio IPC Transport

- **Process Model**: Standalone MCP servers execute in an independent process via
  `subprocess.Popen([sys.executable, "-c", ...], stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=0)`.
- **Stream Framing**: Newline-delimited JSON-RPC 2.0 strings (`{"jsonrpc":"2.0",...}\n`).
- **Channel Segregation**: JSON-RPC traffic flows strictly over `stdin` and `stdout`. Diagnostic
  and debug logs are routed to `stderr` to prevent JSON stream contamination.

---

## Shared Wire Test Helper (`tests/helpers/raw_tcp_client.py`)

To test raw network conditions without high-level HTTP client abstractions (which automatically
buffer or reassemble packets), the test harness relies on the shared utility module
[`tests/helpers/raw_tcp_client.py`](file:///home/src/tests/helpers/raw_tcp_client.py). Promoted
under [PYPOST-1428](https://pypost.atlassian.net/browse/PYPOST-1428), this module exports low-level
wire socket testing primitives for all MCP transport test suites:
- `RawTcpWireClient`: Low-level TCP socket client for frame injection, pipelining, and parsing.
- `parse_jsonrpc_from_response`: Parser extracting JSON-RPC messages from JSON or SSE payloads.

### `RawTcpWireClient` Class API

`RawTcpWireClient` operates directly on physical TCP stream sockets (`socket.AF_INET`,
`socket.SOCK_STREAM`) against loopback endpoints. It manages connection lifecycles, HTTP/1.1 wire
framing, arbitrary byte-level transmission fragmentation, and stream reassembly across packet
chunks.

#### Class Signature & Initialization

```python
class RawTcpWireClient:
    def __init__(self, host: str, port: int, timeout: float = 10.0) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock: socket.socket | None = None
        self.session_id: str | None = None
        self._unread_buffer = bytearray()
```

- **`host`** (`str`): Target hostname or loopback address (typically `"127.0.0.1"`).
- **`port`** (`int`): Target TCP port number allocated for the standalone server.
- **`timeout`** (`float`, default `10.0`): Socket timeout in seconds applied to connect and read
  operations.

**Instance Attributes**:
- `sock: socket.socket | None`: The active underlying operating system socket descriptor, or `None`
  when disconnected.
- `session_id: str | None`: Cached MCP session ID extracted automatically from the `mcp-session-id`
  response header.
- `_unread_buffer: bytearray`: Internal stream buffer preserving unread bytes read ahead during
  framing for subsequent requests.

#### Methods Reference

##### `connect() -> None`
Establishes a physical TCP stream connection (`socket.AF_INET`, `socket.SOCK_STREAM`) to
`(self.host, self.port)` with the configured timeout.

##### `close() -> None`
Gracefully shuts down and closes the underlying socket descriptor. Issues `socket.SHUT_RDWR`
(suppressing `OSError` if the peer has already disconnected or reset) and closes `self.sock`,
resetting it to `None`.

##### Context Manager Protocol (`__enter__` and `__exit__`)
Supports `with RawTcpWireClient(host, port) as client:` syntax. Calls `connect()` on entry and
guarantees deterministic `close()` on block exit.

##### `build_post_request(payload, path="/mcp", session_id=None) -> bytes`
Constructs compliant, raw HTTP/1.1 `POST` request wire bytes with JSON-RPC payload.
- **`payload`** (`dict[str, Any]`): JSON-serializable dictionary representing the JSON-RPC request.
- **`path`** (`str`, default `"/mcp"`): Target HTTP endpoint URI path.
- **`session_id`** (`str | None`, optional): Explicit MCP session ID override; defaults to
  `self.session_id`.
- **Returns** (`bytes`): Formatted raw HTTP/1.1 wire request including `POST`, `Host`,
  `Content-Type: application/json`, `Accept: application/json, text/event-stream`, `Content-Length`,
  `Connection: keep-alive`, and optional `mcp-session-id` headers.

##### `send_fragmented(data: bytes, chunk_size: int = 7, delay: float = 0.0) -> None`
Transmits arbitrary byte sequences sliced into small micro-chunks to simulate extreme network
segmentation and packet boundary fragmentation.
- **`data`** (`bytes`): Raw byte sequence to transmit across the socket.
- **`chunk_size`** (`int`, default `7`): Maximum slice size in bytes per `socket.sendall` call (down
  to 1 byte).
- **`delay`** (`float`, default `0.0`): Optional sleep interval in seconds between slice
  transmissions.

##### `send_all(data: bytes) -> None`
Transmits the entire byte buffer in a single bulk `sendall()` socket write. Used for high-volume
pipelined bursts.
- **`data`** (`bytes`): Raw byte buffer to transmit.

##### `read_http_response() -> tuple[int, dict[str, str], bytes]`
Reads a single complete HTTP/1.1 response from the persistent socket stream.
- **Stream Processing**:
  - Scans `self._unread_buffer` and reads from socket in 4096-byte chunks until the header delimiter
    (`\r\n\r\n`) is encountered.
  - Parses status line into status code integer.
  - Normalizes headers to lower-case keys.
  - Captures `mcp-session-id` into `self.session_id` when present.
  - Decodes chunked transfer encoding (`Transfer-Encoding: chunked`) or bounded `Content-Length`
    bodies.
  - Retains any excess read bytes in `self._unread_buffer` for subsequent pipelined response reads.
- **Returns** (`tuple[int, dict[str, str], bytes]`):
  - `status_code` (`int`): HTTP status code (e.g. `200`, `202`, `404`).
  - `headers` (`dict[str, str]`): Mapping of lower-case HTTP header names to header values.
  - `body_bytes` (`bytes`): Complete decoded payload bytes.
- **Exceptions Raised**:
  - `ConnectionResetError`: Raised if the connection is closed prematurely by peer while waiting for
    header delimiters or chunk data.
  - `socket.timeout`: Raised if the socket read timeout expires before the full response arrives.

### `parse_jsonrpc_from_response` Helper API

```python
def parse_jsonrpc_from_response(body_bytes: bytes) -> list[dict[str, Any]]:
```

#### Overview
Extracts and parses JSON-RPC 2.0 message dictionaries from raw HTTP response bodies. Because MCP
transports may return direct JSON or SSE streams, this helper transparently handles both response
formats.

#### Parameters & Return Types
- **`body_bytes`** (`bytes`): Raw response body bytes received from the wire.
- **Returns** (`list[dict[str, Any]]`): List of parsed JSON-RPC message dictionaries. If no valid
  JSON-RPC payloads are discovered, returns an empty list `[]`.

#### Parsing Logic
1. Decodes `body_bytes` as UTF-8 (with `errors="replace"`).
2. If text starts with `{` and ends with `}`, attempts direct `json.loads(text)`.
3. If not direct JSON, scans lines for Server-Sent Events syntax (`data: ...`), extracting and
   decoding nested JSON payloads from `data:` blocks.

### Usage Patterns in Test Suites

#### 1. Context Manager with Fragmented Frames
```python
from tests.helpers.raw_tcp_client import RawTcpWireClient, parse_jsonrpc_from_response

with RawTcpWireClient(host="127.0.0.1", port=server_port, timeout=10.0) as client:
    # 1. Handshake with fragmented 7-byte chunks
    init_req = client.build_post_request({
        "jsonrpc": "2.0",
        "id": "init-1",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"},
        },
    })
    client.send_fragmented(init_req, chunk_size=7)
    status, headers, body = client.read_http_response()
    assert status == 200
    msgs = parse_jsonrpc_from_response(body)
    assert msgs[0]["id"] == "init-1"

    # 2. Extreme 1-byte micro-chunking
    call_req = client.build_post_request({
        "jsonrpc": "2.0",
        "id": "call-1",
        "method": "tools/call",
        "params": {"name": "echo", "arguments": {"msg": "hello"}},
    })
    client.send_fragmented(call_req, chunk_size=1)
    status, headers, body = client.read_http_response()
    assert status == 200
```

#### 2. Pipelined 100-Request Bursts
```python
from tests.helpers.raw_tcp_client import RawTcpWireClient, parse_jsonrpc_from_response

with RawTcpWireClient(host="127.0.0.1", port=server_port) as client:
    # Perform initial handshake to establish session_id
    # ...
    # Pre-generate 100 pipelined requests
    burst_bytes = bytearray()
    for idx in range(100):
        req = client.build_post_request({
            "jsonrpc": "2.0",
            "id": f"burst-{idx}",
            "method": "tools/list",
            "params": {},
        })
        burst_bytes.extend(req)

    # Blast entire buffer over socket in a single write
    client.send_all(bytes(burst_bytes))

    # Read back 100 responses sequentially from stream
    for idx in range(100):
        status, headers, body = client.read_http_response()
        assert status == 200
        msgs = parse_jsonrpc_from_response(body)
        assert msgs[0]["id"] == f"burst-{idx}"
```

---

## Stress Test Scenarios & Invariants

The test suite in
[`test_mcp_standalone_wire_ipc_repro.py`](../../tests/test_mcp_standalone_wire_ipc_repro.py)
validates four critical architectural stress scenarios:

### 1. TCP Packet Fragmentation Resilience

- **Failure Mode**: TCP is a stream-oriented protocol. Packet boundaries are non-deterministic
  and can split across headers, within JSON keys, or across multibyte UTF-8 characters. If an
  ASGI server or stream parser assumes headers or payloads arrive in a single read call, the server
  fails with protocol syntax errors or desynchronization.
- **Verification Strategy**:
  1. Standalone server starts on an ephemeral allocated port via `allocate_tcp_port()`.
  2. `initialize` request is fragmented into 7-byte chunks across the wire.
  3. `notifications/initialized` is fragmented into 7-byte chunks.
  4. `tools/list` request is fragmented into 7-byte chunks.
  5. `tools/call` request is transmitted in **1-byte micro-chunks** (`chunk_size=1`).
- **Invariant**: The server buffers fragmented incoming packets, accurately reconstructs HTTP
  headers and bodies, dispatches tool execution through `MCPServerImpl`, and returns valid JSON-RPC
  responses.

### 2. Pipelined Burst Throughput (100-Request Bursts)

- **Failure Mode**: In high-velocity agent environments, clients stream back-to-back requests over
  an open keep-alive connection. Naive servers may suffer socket buffer overruns, ASGI worker
  starvation, connection resets (`ECONNRESET`), or dropped requests.
- **Verification Strategy**:
  1. Establish session via handshake over raw TCP keep-alive connection.
  2. Pre-generate 100 complete HTTP/JSON-RPC requests (`pipelined-0` through `pipelined-99`).
  3. Concatenate all 100 requests into a single continuous byte buffer and blast it over the wire
     using a single `client.send_all()` socket write.
  4. Read responses sequentially from the socket stream.
- **Invariant**: Exactly 100 HTTP 200 responses are returned in order, with zero socket stalls,
  resets, or dropped IDs.

### 3. Stdio Pipe Buffer Deadlock Avoidance (>64KB `PIPE_BUF`)

- **Failure Mode**: Operating system pipes have fixed kernel buffer capacities (Linux `PIPE_BUF`
  atomic write limit is 4096 bytes; standard pipe buffer capacity is 65,536 bytes / 64KB).
  If a client writes large payloads or rapid bursts to `stdin` without draining `stdout`
  concurrently, the kernel pipe buffer fills up, causing a permanent deadlock where both
  processes block on I/O.
- **Verification Strategy**:
  1. Launch standalone MCP server in an external Python subprocess running
     `mcp.server.stdio.stdio_server`.
  2. Spawn two dedicated background drainer threads:
     - `stdout_worker`: Continuously drains `process.stdout` using line iterators, parsing JSON-RPC
       messages into a thread-safe dictionary under a lock.
     - `stderr_worker`: Continuously drains `process.stderr` into a log buffer.
  3. Send initial handshake (`initialize`, `notifications/initialized`).
  4. Inject a burst of 50 requests, with requests 41–50 containing large 70KB payloads
     (`"X" * 70000`), exceeding the 64KB OS pipe buffer limit.
  5. Close `process.stdin` and assert clean exit with return code 0.
- **Invariant**: All 50 responses (including the 70KB payloads) are received intact without payload
  corruption or truncation. The server process terminates cleanly on `stdin` EOF.

### 4. Rapid Teardown & Immediate Port Re-Binding Under Hammer Load

- **Failure Mode**: Under heavy traffic, tearing down a server can leave TCP ports in `TIME_WAIT` or
  leak socket descriptors, causing subsequent `bind()` calls to fail with
  `OSError: [Errno 98] Address already in use` (`EADDRINUSE`).
- **Verification Strategy**:
  1. Start standalone MCP server on an allocated loopback port.
  2. Launch 3 concurrent "hammer" threads firing rapid TCP connect/send/close loops against
     `POST /mcp`.
  3. While hammer traffic is actively in flight, invoke `manager.stop_server()`.
  4. Join hammer threads and assert no unhandled exceptions.
  5. Verify the port can immediately be re-bound with `SO_REUSEADDR`.
  6. Immediately spin up a second `MCPServerManager` instance binding to the identical port,
     asserting successful startup and listener readiness.
- **Invariant**: Shutdown is graceful and immediate under active load; sockets and worker threads
  are released cleanly without port exhaustion or `EADDRINUSE`.

---

## Test Execution Guide

All tests must be run exclusively via `make` targets. Never invoke `pytest` or `pip` directly.

### Running Wire & Stdio Stress Tests

```bash
# Run standalone wire IPC and stdio stress test suite
make test PYTEST_ARGS='tests/test_mcp_standalone_wire_ipc_repro.py'

# Run unit tests for shared raw_tcp_client test helper
make test PYTEST_ARGS='tests/test_raw_tcp_client_helper.py'

# Run wire stress tests together with helper tests and standalone execution tests
make test PYTEST_ARGS='tests/test_raw_tcp_client_helper.py tests/test_mcp_standalone_execution_repro.py tests/test_mcp_standalone_wire_ipc_repro.py'

# Run all MCP-related test suites
make test PYTEST_ARGS='tests/test_mcp*.py'
```

### Running Full Quality Gates

```bash
# Run linting (flake8, doc linting, relative link verification)
make lint

# Run type checking (mypy baseline gate)
make typecheck

# Combined quality gate (lint + fast tests + verify-ai-tasks)
make check
```

---

## Related Documentation

- Multi-Server Registry Architecture: [mcp_server_registry.md](mcp_server_registry.md)
- Model Context Protocol Architecture & Security: [mcp.md](mcp.md)
- Inbound MCP Trust Model: [mcp_trust_model.md](mcp_trust_model.md)
- MCP Integration Guide: [mcp_integration.md](mcp_integration.md)
