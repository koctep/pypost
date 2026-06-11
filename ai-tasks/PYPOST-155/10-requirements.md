# PYPOST-155: Legacy SSE `/messages` method filtering

## Goals

Reduce low-level ASGI boilerplate in the legacy MCP HTTP+SSE transport by relying on Starlette
routing for HTTP method enforcement where the framework supports it.

## User Stories

- As a **maintainer**, I want legacy `/sse/messages` to reject non-POST requests without custom
  405 response code inside the handler, so routing behavior stays consistent with other MCP paths.
- As an **operator**, I expect wrong HTTP methods on legacy MCP endpoints to return 405, unchanged
  from current behavior.

## Definition of Done

- Legacy `/messages` uses Starlette `Route` with `methods=["POST"]` instead of `Mount` plus manual
  method checks.
- Manual 405 response construction for `/messages` is removed.
- Existing routing tests still pass (405 on GET `/sse/messages`, POST-only acceptance).
- Same layout applied wherever legacy SSE is duplicated (`MCPServerImpl`, `MetricsServer`).
- Developer docs note the routing approach and remaining ASGI wrappers.

## Task Description

Follow-up from PYPOST-21: the `/messages` workaround used `Mount` because method filtering was
thought unavailable. Starlette `Route` accepts ASGI callables and supports `methods`, so the
workaround can be replaced with declarative routing.

## Q&A

- **Q:** Does this change MCP client behavior?
  - **A:** No — only internal routing; HTTP status codes for wrong methods stay 405.
