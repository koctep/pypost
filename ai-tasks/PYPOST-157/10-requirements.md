# PYPOST-157: Clean up legacy MessagesEndpoint response handling

## Goals

Reduce maintenance risk in the legacy MCP HTTP+SSE transport by removing ad-hoc HTTP response
formatting from the messages endpoint. Starlette routing should own method filtering and error
responses; the messages handler should focus on MCP post-message handling only.

## User Stories

- As a **maintainer**, I want `MessagesEndpoint` to avoid duplicating Starlette response logic so
  framework upgrades and routing changes stay localized.
- As a **maintainer**, I want shared legacy SSE code to use consistent, module-level imports so
  endpoint behavior is easy to read and test in isolation.

## Definition of Done

- `MessagesEndpoint` does not manually format HTTP responses (no `_send_response`, no raw ASGI
  405 bodies for method checks).
- Non-POST requests to the messages path return 405 via Starlette `Route` method filtering
  (established in PYPOST-155).
- `starlette.responses.Response` is not imported or used inside `MessagesEndpoint`; any Response
  usage for the legacy sub-app lives at module scope outside that class.
- Regression test covers the above; existing MCP legacy SSE tests pass.
- Developer docs describe the split between routing-owned 405s and ASGI post-message handling.

## Task Description

Follow-up from PYPOST-21 / PYPOST-155 / PYPOST-156: endpoint classes were extracted to
`mcp_legacy_sse.py`, but tech debt tracked manual response formatting and conditional Response
imports on `MessagesEndpoint`. This task closes that debt.

## Q&A

- **Q:** Does this change MCP client behavior?
  - **A:** No — internal cleanup; HTTP paths and status codes unchanged.
