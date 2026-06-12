# PYPOST-161: ASGI compatibility test coverage

## Goals

Close technical debt from PYPOST-21 by adding automated regression tests that Starlette
registers MCP and metrics endpoints as direct ASGI applications, preventing the
`TypeError: 'NoneType' object is not callable` failure when low-level transports write via
`send` instead of returning `Response`.

## User Stories

- As a **maintainer**, I want tests that legacy SSE `MessagesEndpoint` routes are direct ASGI
  callables, so Starlette does not wrap them in `request_response`.
- As a **maintainer**, I want tests that Streamable HTTP `/mcp` routes on both MCP and metrics
  servers use direct ASGI delegation.
- As a **maintainer**, I want tests that the metrics server exposes `/metrics`, `/mcp`, and
  legacy `/sse` ASGI surfaces with the expected structure.
- As an **operator**, I expect no behavior change; tests document and lock current routing only.

## Definition of Done

- `tests/test_mcp_asgi_compatibility.py` covers legacy SSE, Streamable HTTP, and metrics mount
  ASGI registration for `MCPServerImpl` and `MetricsServer`.
- POST to legacy `/messages` completes without `TypeError` when transport is mocked.
- Existing MCP and metrics tests pass.
- Developer testing docs list the new coverage.

## Task Description

Follow-up from `ai-tasks/PYPOST-21/40-tech-debt.md`. PYPOST-155–160 refactored routing and
module extraction; PYPOST-158 added SSE close and 405 guards. This task adds the missing ASGI
compatibility layer.

## Q&A

- **Q:** Does this change production routing?
  - **A:** No — tests only unless a regression is found.
