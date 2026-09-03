# PYPOST-1105 Requirements

## Business reason

Unit tests and in-process ASGI tests cover MCP proxy behavior, but they do not
prove that transport framing, sockets, Uvicorn lifecycle, and process
boundaries work together. Wire-level regressions can therefore reach users
despite passing fast tests.

## User stories

- As a maintainer, I want a real Streamable HTTP upstream process so chunked
  response handling is tested over a socket.
- As a maintainer, I want a real legacy SSE upstream process so proxy transport
  selection and event-stream initialization are verified end to end.
- As a CI operator, I want the expensive process tests isolated behind the
  existing `slow` marker and bounded timeouts.

## Functional requirements

1. Add `tests/test_mcp_proxy_live_integration.py`.
2. Start the upstream MCP server in a separate background process using Uvicorn
   and an allocated loopback TCP port.
3. Start `MCPProxyServerImpl` in a second background process using Uvicorn.
4. Verify a downstream Streamable HTTP client can list and call a tool through
   a proxy whose upstream transport is Streamable HTTP.
5. Make the Streamable HTTP upstream return a response large enough to exercise
   wire streaming/chunking rather than only a tiny in-memory result.
6. Verify a downstream Streamable HTTP client can list and call a tool through
   a proxy whose upstream transport is legacy SSE.
7. Assert returned tool identity and payload content at the downstream client.
8. Ensure both child processes are stopped and joined in all test outcomes.

## Non-functional requirements

- Tests must use only loopback networking and dynamically allocated ports.
- Tests must be marked `slow` and declare a bounded module timeout.
- Process startup and teardown must be bounded; a stuck child must not hang CI.
- The harness must not rely on global test order or external services.
- The tests must run through `make test-slow` and remain excluded from the fast
  default `make test` suite.
- Test source lines and task documentation must stay within 100 characters.

## In scope

- A process-safe Uvicorn harness local to the new test module.
- Real Streamable HTTP and legacy SSE upstream proxy round trips.
- Wire payload assertions and deterministic child cleanup.

## Out of scope

- Production MCP proxy changes.
- External network, TLS, authentication, or load-balancer coverage.
- Connection pooling or upstream session reuse (PYPOST-1101).
- Additional UI, metrics, or protocol features.

## Acceptance criteria

- The new module contains one slow test for Streamable HTTP wire forwarding and
  one slow test for SSE wire forwarding.
- Both tests use separate live processes for upstream and proxy servers.
- The Streamable HTTP case validates a large returned payload.
- The SSE case validates a real event-stream-backed tool call.
- `make test-slow PYTEST_ARGS="tests/test_mcp_proxy_live_integration.py"` passes.
- Fast proxy tests, lint, typecheck, and AI-task verification remain passing.
- No child process or socket remains after the tests finish.
