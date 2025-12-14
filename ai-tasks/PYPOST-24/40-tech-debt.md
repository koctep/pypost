# PYPOST-24: Technical Debt Analysis

## Shortcuts Taken

- To fix the `/messages` issue, manual method control (POST) inside the ASGI application and manual
  405 response were used, since `Mount` in Starlette does not support method filtering (unlike
  `Route`). This is a somewhat "low-level" solution.

## Code Quality Issues

- `SSEEndpoint` and `MessagesEndpoint` classes are defined inside `create_app` method. This
  hinders reuse and isolated testing. They should be moved to module level.
- `MessagesEndpoint` now has a dependency on `starlette.responses` (import inside method if
  `Response` object were used) or manual response formatting, which duplicates framework logic.

## Missing Tests

- No automated tests for this specific behavior (correct SSE connection closure and 405 return for
  non-POST requests to `/messages`). Testing was done manually or assumed covered by MCP
  integration tests.

## Performance Concerns

- None. Using `Mount` and direct ASGI invocation is even more efficient than the `request_response`
  wrapper in `Route`.

## Follow-up Tasks

- Refactor `MCPServerImpl`: move `SSEEndpoint` and `MessagesEndpoint` out of `create_app` method.
- Add tests for ASGI compatibility of endpoints.
