# PYPOST-560: MCPClientService asyncio.run hangs on live SSE initialize

## Goals

Fix the sync wrapper `MCPClientService.run` so in-app MCP client requests work against live servers without hanging. Currently, `MCPClientService.run` wraps `sse_client` (anyio task groups) in `asyncio.run`, which hangs after `initialize` when talking to a live MCP server. The goal is to replace `asyncio.run` + `asyncio.wait_for` with `anyio.run` + `anyio.fail_after` and use `ClientSession` as an async context manager for clean teardown.

## User Stories

- **As a user / developer**, I want `MCPClientService` to reliably list tools and call tools against a live MCP server without hanging.
- **As a developer**, I want clean teardown of the `ClientSession` so that resources are not leaked.
- **As a maintainer**, I want regression tests that verify `MCPClientService` works against a live streamable HTTP server over SSE.

## Definition of Done

- [x] `MCPClientService.run` replaced `asyncio.run` + `asyncio.wait_for` with `anyio.run` + `anyio.fail_after`.
- [x] `ClientSession` is used as an async context manager in `MCPClientService._run_async` for clean teardown.
- [x] Regression test `test_mcp_client_service_list_tools_over_live_streamable_http` added in `tests/test_mcp_server_integration.py`.
- [x] All unit and integration tests pass successfully.
- [x] Developer documentation updated to reflect the changes.

## Task Description

`MCPClientService.run` wraps `sse_client` (anyio task groups) in `asyncio.run`, which hangs after `initialize` when talking to a live MCP server. Integration tests use `anyio.run` + `ClientSession` directly. Fix the sync wrapper so in-app MCP client requests work against live servers.

## Q&A

- **Why does `asyncio.run` hang?**
  - `sse_client` uses anyio task groups under the hood. Mixing `asyncio.run` with anyio-based libraries can cause event loop mismatch or task group scheduling issues, leading to hangs during or after initialization.
- **How does `anyio.run` solve this?**
  - `anyio.run` natively supports anyio task groups and runs them on the selected backend (asyncio by default), preventing scheduling mismatches and hangs.
