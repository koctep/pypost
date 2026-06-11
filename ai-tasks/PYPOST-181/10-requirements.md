# PYPOST-181: Live MCP integration tests for MCP test collection

## Goals

PYPOST-180 added shared loaders and groundwork tests for `examples/collections/mcp.json`
and `config/test/environments.json`. Contributors still need automated proof that the
committed collection's exposed tools work over a live Streamable HTTP MCP session
(`list_tools`, `call_tool`) so regressions in tool registration or protocol handling are
caught in CI.

## User Stories

- As a **contributor**, I want CI to run live MCP round-trips using the committed test
  collection so collection changes cannot break agent tool discovery or invocation.
- As a **maintainer**, I want integration tests to reuse PYPOST-180 helpers rather than
  duplicating collection paths and expected tool names.
- As a **test author**, I want deterministic execution (mocked upstream HTTP) so CI does not
  require a running PyPost app or metrics server on ports 1080/9080.

## Definition of Done

- [x] Integration tests load the MCP test collection via `tests/helpers/mcp_test_collection.py`.
- [x] Live MCP server starts on an ephemeral port with collection-derived exposed tools.
- [x] `list_tools` returns `sse_probe_metrics` and `sse_probe_main`.
- [x] `call_tool` succeeds for each exposed collection tool with structured JSON envelope.
- [x] `call_tool` delegates to `RequestService` with the matching collection request.
- [x] Developer documentation describes the new test module and focused run command.
- [x] Full test suite passes.

## Task Description

Follow-up from [PYPOST-25](https://pypost.atlassian.net/browse/PYPOST-25) /
[PYPOST-180](https://pypost.atlassian.net/browse/PYPOST-180): add live MCP integration tests
that load the committed collection and execute requests via MCP (`list_tools`, `call_tool`).
Align with `tests/test_mcp_server_integration.py` harness conventions.

## Q&A

- **Q:** Must tests hit real SSE endpoints on 1080/9080?
  **A:** No — MCP protocol is live; upstream HTTP is mocked via `RequestService` for CI
  determinism (same pattern as PYPOST-368/551).
- **Q:** Is the List Tools collection request tested via MCP?
  **A:** No — it is not `expose_as_mcp`; groundwork tests already assert it stays internal.
