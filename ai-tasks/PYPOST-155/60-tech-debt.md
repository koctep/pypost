# PYPOST-155: Technical Debt Analysis

## Resolved

- **POST + 405 on `/messages`**: Replaced `Mount` + manual ASGI 405 with `Route(..., methods=["POST"])`.

## Remaining (non-blockers)

- **Nested MCP endpoints** — Jira: [PYPOST-156](https://pypost.atlassian.net/browse/PYPOST-156):
  `SSEEndpoint` and `MessagesEndpoint` remain nested in `_create_sse_app`; extract to module scope.
- **SSE close + 405 coverage** — Jira: [PYPOST-158](https://pypost.atlassian.net/browse/PYPOST-158):
  Broader automated coverage for SSE shutdown still deferred.
- **Mount + direct ASGI for SSE stream** — Jira: [PYPOST-159](https://pypost.atlassian.net/browse/PYPOST-159):
  GET `/sse/` still uses ASGI wrapper via `handle_sse_get`; acceptable for long-lived SSE.

## Blocker review

**SAFE TO CLOSE** — acceptance criteria met; remaining items are pre-existing follow-ups with Jira links.
