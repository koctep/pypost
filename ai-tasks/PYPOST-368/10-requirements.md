# PYPOST-368: MCP Server Integration Tests

## Goals

Close the PYPOST-38 technical-debt item that flagged missing automated integration coverage
for the embedded MCP server. Developers need pytest tests that start a real uvicorn-backed MCP
server and verify tool listing and invocation over the SSE transport, so protocol and routing
regressions are caught in CI.

## User Stories

- **As a developer**, I want integration tests that start the MCP server on a free local port
  so the full SSE handshake and message POST path are exercised.
- **As a developer**, I want tests that call `list_tools` and `call_tool` via the official MCP
  client SDK so tool registration and execution are verified end-to-end.
- **As a maintainer**, I want every new test to declare an explicit pytest timeout so the
  suite cannot hang in CI.

## Definition of Done

- [x] `tests/test_mcp_server_integration.py` starts a live MCP server and verifies
  `list_tools` and `call_tool` over SSE.
- [x] At least one test exercises `MCPServerManager` (production thread + uvicorn lifecycle).
- [x] All tests declare `pytest.mark.timeout` (module-level `pytestmark`).
- [x] Focused pytest run passes.
- [x] Developer docs reference the integration test module.

## Task Description

Source: `ai-tasks/PYPOST-38/60-tech-debt.md` — "No integration tests that start the MCP
server and verify tool invocation." PYPOST-367 added unit-level coverage; this ticket adds
live SSE round-trip tests.

## Q&A

- **Is full HTTP request execution to external URLs required?**
  - No. `RequestService` may be mocked so tests stay deterministic; the integration surface
    is MCP protocol + server startup, not outbound HTTP.
- **Must `MCPClientService` be used?**
  - Tests use `mcp` SDK `sse_client` + `ClientSession` with `anyio.run`, which matches the
    live transport. `MCPClientService` sync wrapper limitations are tracked as follow-up debt.
