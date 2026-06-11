# PYPOST-156: Technical Debt Analysis

## Resolved

- **Nested MCP endpoints**: `SSEEndpoint` and `MessagesEndpoint` moved to
  `pypost/core/mcp_legacy_sse.py` with `build_legacy_sse_app` factory.

## Remaining (non-blockers)

- **SSE close + 405 coverage** — Jira: [PYPOST-158](https://pypost.atlassian.net/browse/PYPOST-158):
  Broader automated coverage for SSE shutdown still deferred.
- **Mount + direct ASGI for SSE stream** — Jira: [PYPOST-159](https://pypost.atlassian.net/browse/PYPOST-159):
  GET `/sse/` still uses ASGI wrapper via `handle_sse_get`; acceptable for long-lived SSE.
- **MessagesEndpoint responses** — Jira: [PYPOST-157](https://pypost.atlassian.net/browse/PYPOST-157):
  Response handling improvements deferred.

## Blocker review

**SAFE TO CLOSE** — acceptance criteria met; remaining items are pre-existing follow-ups with
Jira links.
