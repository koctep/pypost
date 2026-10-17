# PYPOST-1428: Technical Debt Analysis

## Shortcuts Taken

None. The extraction of `RawTcpWireClient` and `parse_jsonrpc_from_response` from `tests/test_mcp_standalone_wire_ipc_repro.py` into the shared helper `tests/helpers/raw_tcp_client.py` was executed as a clean, complete, and production-grade refactoring.

- Full functional parity was preserved, including socket context manager lifecycle, custom endpoint URI path overrides, session ID extraction and override, RFC 9112 chunked transfer encoding decoding, and Content-Length bounded reading.
- A dedicated unit test suite (`tests/test_raw_tcp_client_helper.py`) was created, covering all classes, methods, edge cases, and error handling.
- `tests/test_mcp_standalone_wire_ipc_repro.py` was cleanly migrated to import from `tests.helpers.raw_tcp_client` without monkey-patching or temporary backward-compatibility aliases.
- No temporary workarounds or shortcuts were introduced during development.

## Code Quality Issues

All identified items are classified as **NON-BLOCKER** (architectural boundaries suitable for test helpers):

1. **Synchronous Blocking Sockets Without Async/Event-Loop Integration (NON-BLOCKER)**:
   - `RawTcpWireClient` relies on standard synchronous blocking sockets (`socket.socket(socket.AF_INET, socket.SOCK_STREAM)`) with explicit socket timeouts (`sock.settimeout(timeout)`).
   - This synchronous design is optimal for deterministic unit and integration test assertions where test steps proceed sequentially. However, it cannot be directly integrated into an `asyncio` or `Qt` event-loop without dedicated worker threads or non-blocking socket polling (`select`/`epoll`).

2. **Hardcoded IPv4 Address Family (`AF_INET`) (NON-BLOCKER)**:
   - `RawTcpWireClient.connect()` creates sockets using `socket.AF_INET`.
   - While standard for local testing against `127.0.0.1`, it cannot directly establish connections to IPv6 addresses (such as `::1`) without refactoring to use `socket.getaddrinfo` or configurable socket families.

3. **Hand-Crafted Wire-Level HTTP Framing Parser (NON-BLOCKER)**:
   - `RawTcpWireClient.read_http_response()` implements a custom, minimal HTTP/1.1 wire parser specifically tuned for raw frame injection, chunked transfer decoding, and SSE body extraction.
   - It intentionally omits support for complex HTTP/1.1 features not required in test scenarios (e.g. multi-line header folding, trailer fields, or gzip/deflate compression). This boundary is intentional to keep test dependencies minimal, but represents a known scope constraint.

## Missing Tests

All identified items are classified as **NON-BLOCKER** (future coverage expansions):

1. **IPv6 Loopback Transport Coverage (NON-BLOCKER)**:
   - Existing unit and integration tests validate IPv4 loopback (`127.0.0.1`).
   - Automated test coverage validating `RawTcpWireClient` connecting to standalone MCP servers bound to IPv6 loopback (`::1`, `AF_INET6`) is not yet present. Tracked in [PYPOST-1431](https://pypost.atlassian.net/browse/PYPOST-1431).

2. **Malformed JSON-RPC and Wire Framing Fuzzing Suite (NON-BLOCKER)**:
   - `tests/test_raw_tcp_client_helper.py` verifies empty, malformed, and non-JSON payloads returning empty message lists.
   - However, comprehensive fuzzing of server wire resilience (e.g. truncated chunk boundaries, corrupted hex chunk sizes, invalid JSON-RPC types, or deep recursion payloads injected over raw TCP sockets) is not part of this extraction task. Tracked in [PYPOST-1430](https://pypost.atlassian.net/browse/PYPOST-1430).

3. **High-Throughput Multi-Megabyte Stress Scenarios (NON-BLOCKER)**:
   - The test suites exercise packet fragmentation (1-byte and 7-byte slices) and burst pipelining with payloads up to dozens of kilobytes.
   - Extreme multi-megabyte burst throughput testing to evaluate garbage collection and memory saturation under high load is deferred to dedicated stress benchmarks.

## Performance Concerns

All identified items are classified as **NON-BLOCKER** (minor memory allocations that do not affect test runtimes):

1. **`bytearray` Slice Copies for High-Throughput Responses (NON-BLOCKER)**:
   - `RawTcpWireClient` maintains stream state using a `bytearray` (`self._unread_buffer`) and performs slicing operations (`self._unread_buffer = body[content_length:]`, `body = body[crlf + 2 + chunk_len + 2:]`).
   - For standard test payloads (bytes to kilobytes), memory allocation overhead is negligible. In extreme burst scenarios with multi-megabyte responses, replacing slice copies with zero-copy `memoryview` slices would reduce memory churn and garbage collection pressure. Tracked in [PYPOST-1432](https://pypost.atlassian.net/browse/PYPOST-1432).

2. **Sequential Transmission Loops (NON-BLOCKER)**:
   - `RawTcpWireClient.send_fragmented()` uses a sequential loop with `time.sleep(delay)` and `sock.sendall(chunk)`.
   - This synchronous pacing is deterministic and ideal for testing fragmentation reassembly, but introduces cumulative wall-clock delay if large payloads are sent with non-zero delays across large test matrices.

## Follow-up Tasks

All follow-up items are non-blocking enhancements tracked in existing Jira sprint tickets:

1. **[PYPOST-1431](https://pypost.atlassian.net/browse/PYPOST-1431): Add IPv6 Socket Transport Coverage for Standalone MCP Servers**:
   - *Status*: NON-BLOCKER (Feature Enhancement / Test Coverage)
   - *Description*: Extend `RawTcpWireClient` to dynamically resolve socket address families (`socket.getaddrinfo` or `AF_INET6` configuration) and add test coverage validating standalone MCP servers over IPv6 loopback (`::1`).
   - *Type*: Test Coverage
   - *Priority*: Low
   - *Story Points*: 2

2. **[PYPOST-1432](https://pypost.atlassian.net/browse/PYPOST-1432): Zero-Copy Memory Optimization for RawTcpWireClient**:
   - *Status*: NON-BLOCKER (Performance Optimization)
   - *Description*: Refactor `RawTcpWireClient._unread_buffer` and chunk parsing logic from `bytearray` slicing to `memoryview` zero-copy buffer slicing to optimize memory allocation and GC overhead during high-throughput burst tests.
   - *Type*: Performance Optimization
   - *Priority*: Low
   - *Story Points*: 2

3. **[PYPOST-1430](https://pypost.atlassian.net/browse/PYPOST-1430): Implement Malformed JSON-RPC and Wire Framing Fuzzing Suite**:
   - *Status*: NON-BLOCKER (Test Coverage / Resilience)
   - *Description*: Implement a negative fuzzing test suite using `RawTcpWireClient` to exercise standalone MCP server wire parsers against invalid chunk boundaries, broken hex sizes, illegal JSON-RPC envelopes, and truncated TCP frames.
   - *Type*: Test Coverage
   - *Priority*: Medium
   - *Story Points*: 3
