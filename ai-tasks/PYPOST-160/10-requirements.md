# PYPOST-160: Move SSE endpoints out of MCPServerImpl.create_app

## Goals

Improve maintainability of the legacy MCP HTTP+SSE transport by removing nested endpoint
classes from `MCPServerImpl.create_app` / `_create_sse_app`, making endpoints reusable and
testable in isolation.

## User Stories

- As a **maintainer**, I want `SSEEndpoint` and `MessagesEndpoint` defined outside
  `create_app` so I can import and test them without constructing a full server factory.
- As a **maintainer**, I want a single shared implementation for legacy SSE routing used by
  both the request-tools MCP server and the metrics MCP server.

## Definition of Done

- `SSEEndpoint` and `MessagesEndpoint` are no longer nested inside `_create_sse_app` or
  `create_app`.
- `MCPServerImpl` delegates legacy SSE routing to the shared module.
- Unit tests can import endpoints and assert routing without going through `create_app`.
- Existing MCP routing tests continue to pass.

## Source

Follow-up from PYPOST-21 tech debt (`ai-tasks/PYPOST-21/40-tech-debt.md`). Implementation
delivered in [PYPOST-156](https://pypost.atlassian.net/browse/PYPOST-156); this task verifies
and closes the duplicate tracker item.

## Q&A

- **Q:** Does this change MCP client behavior?
  - **A:** No — internal refactor only; HTTP paths and status codes unchanged.
