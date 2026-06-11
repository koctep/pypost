# PYPOST-157: Technical Debt Analysis

## Resolved

- **MessagesEndpoint manual responses**: Removed in PYPOST-155; verified in
  `pypost/core/mcp_legacy_sse.py`. `MessagesEndpoint` delegates only to
  `SseServerTransport.handle_post_message`. Method mismatches return 405 from Starlette routing.
- **Conditional / in-method Response imports**: Not used by `MessagesEndpoint`. Module-level
  `Response` import serves `handle_sse_get` only.

## Remaining (non-blockers)

- **SSE close + 405 coverage** — Jira: [PYPOST-158](https://pypost.atlassian.net/browse/PYPOST-158):
  Broader automated coverage for SSE shutdown still deferred.
- **Mount + direct ASGI for SSE stream** — Jira: [PYPOST-159](https://pypost.atlassian.net/browse/PYPOST-159):
  GET `/sse/` still uses ASGI wrapper via `handle_sse_get`; acceptable for long-lived SSE.

## Blocker review

**SAFE TO CLOSE** — acceptance criteria met; no new blockers.
