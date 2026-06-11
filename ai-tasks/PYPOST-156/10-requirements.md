# PYPOST-156: Extract legacy SSE endpoints to module scope

## Goals

Improve maintainability of the legacy MCP HTTP+SSE transport by making endpoint classes
reusable and testable without constructing a full server application factory.

## User Stories

- As a **maintainer**, I want `SSEEndpoint` and `MessagesEndpoint` defined at module scope so
  I can import and test them in isolation.
- As a **maintainer**, I want a single shared implementation for legacy SSE routing used by
  both the request-tools MCP server and the metrics MCP server.

## Definition of Done

- `SSEEndpoint` and `MessagesEndpoint` are no longer nested inside `_create_sse_app`.
- Both `MCPServerImpl` and `MetricsServer` use the shared module-level endpoints.
- Unit tests can import endpoints and assert routing without going through `create_app`.
- Existing MCP routing tests continue to pass (405 on wrong methods, POST `/messages`).

## Task Description

Follow-up from PYPOST-21 / PYPOST-155: routing was simplified with Starlette `Route`, but
endpoint classes remained nested inside `_create_sse_app`, blocking reuse and isolated tests.

## Q&A

- **Q:** Does this change MCP client behavior?
  - **A:** No — internal refactor only; HTTP paths and status codes unchanged.
