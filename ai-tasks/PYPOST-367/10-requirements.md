# PYPOST-367: Unit Tests for MCPServerImpl and MCP Routing

## Goals

Close the PYPOST-38 technical-debt item that flagged missing automated coverage for the MCP
server implementation and its HTTP routing. Developers need fast, deterministic pytest coverage
so MCP tool registration, execution, and route layout regressions are caught in CI without
starting a live SSE session.

## User Stories

- **As a developer**, I want unit tests for `MCPServerImpl` so tool registration, schema
  generation, and `call_tool` behavior are verified with mocked `RequestService`.
- **As a developer**, I want unit tests for MCP HTTP routing so `/sse` and `/sse/messages`
  are mounted correctly and wrong HTTP methods return 405 without a live MCP client.
- **As a maintainer**, I want every new test to declare an explicit pytest timeout so the
  suite cannot hang in CI.

## Definition of Done

- [x] `tests/test_mcp_server_impl.py` covers `MCPServerImpl` tool map, `list_tools`,
  `call_tool`, metrics hooks, script log/error formatting, and template injection.
- [x] The same module covers MCP routing: Starlette mount structure and HTTP method guards
  (no live SSE).
- [x] All tests declare `pytest.mark.timeout` (module-level `pytestmark`).
- [x] `make test` / focused pytest run passes.
- [x] Developer docs reference the automated MCP unit test module.

## Task Description

Source: `ai-tasks/PYPOST-38/60-tech-debt.md` — "No unit tests for `MCPServerImpl` or MCP
routing." Prior work (PYPOST-139/142) added core `MCPServerImpl` tests; this ticket completes
routing coverage and documents the regression surface.

## Q&A

- **Are integration tests with a live MCP client in scope?**
  - No. PYPOST-368 tracks integration coverage. This ticket is unit-level only.
- **Must GET `/sse` be exercised end-to-end?**
  - No. GET `/sse` blocks on SSE handshake; routing tests inspect the route table and verify
    method guards on non-streaming paths.
