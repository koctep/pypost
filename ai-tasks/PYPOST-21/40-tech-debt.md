# PYPOST-21: Technical Debt Analysis


## Shortcuts Taken

- **POST + 405 on `/messages`** ([PYPOST-155](https://pypost.atlassian.net/browse/PYPOST-155)):
  Starlette `Mount` lacks method filtering, so the fix uses explicit POST handling and manual 405
  responses inside the ASGI app — workable but low-level.

## Code Quality Issues

- **Nested MCP endpoints** ([PYPOST-156](https://pypost.atlassian.net/browse/PYPOST-156)):
  `SSEEndpoint` and `MessagesEndpoint` are defined inside `create_app`, which blocks reuse and
  focused tests; move them to module scope.
- **MessagesEndpoint responses** ([PYPOST-157](https://pypost.atlassian.net/browse/PYPOST-157)):
  Depends on `starlette.responses` with conditional imports or manual formatting, duplicating what
  `Route` would normally provide.

## Missing Tests

- **SSE close + 405 on `/messages`** ([PYPOST-158](https://pypost.atlassian.net/browse/PYPOST-158)):
  No automated coverage for correct SSE shutdown and 405 on non-POST `/messages`; verified manually
  or assumed via MCP integration tests.

## Performance Concerns

- **Mount + direct ASGI** ([PYPOST-159](https://pypost.atlassian.net/browse/PYPOST-159)):
  No issues; this path is at least as efficient as a `request_response` wrapper on `Route`.

## Follow-up Tasks

- Refactor `MCPServerImpl`: move `SSEEndpoint` and `MessagesEndpoint` out of `create_app`.
  — [PYPOST-160](https://pypost.atlassian.net/browse/PYPOST-160)
- Add tests for ASGI compatibility of endpoints.
  — [PYPOST-161](https://pypost.atlassian.net/browse/PYPOST-161)
