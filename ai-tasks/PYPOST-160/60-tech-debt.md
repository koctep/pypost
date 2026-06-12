# PYPOST-160: Technical Debt Analysis

## Resolved

- **Nested MCP endpoints in create_app**: Completed in
  [PYPOST-156](https://pypost.atlassian.net/browse/PYPOST-156). `SSEEndpoint` and
  `MessagesEndpoint` live in `pypost/core/mcp_legacy_sse.py`; `MCPServerImpl._create_sse_app`
  delegates to `build_legacy_sse_app`.

## Remaining (non-blockers)

Pre-existing follow-ups with Jira links — no new items:

- **SSE close + 405 coverage** — [PYPOST-158](https://pypost.atlassian.net/browse/PYPOST-158)
- **Mount + direct ASGI for SSE stream** — [PYPOST-159](https://pypost.atlassian.net/browse/PYPOST-159)
- **MessagesEndpoint responses** — [PYPOST-157](https://pypost.atlassian.net/browse/PYPOST-157)

## Blocker review

**SAFE TO CLOSE** — PYPOST-160 acceptance criteria satisfied by PYPOST-156; no code delta
required for this issue.
