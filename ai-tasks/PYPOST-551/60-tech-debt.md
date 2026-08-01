# PYPOST-551: Technical Debt (Step 6)

## Resolved in this task

- Primary MCP network transport aligned with current MCP spec (Streamable HTTP at `/mcp`).
- In-app `MCPClientService` and integration tests use `streamable_http_client`.

## Remaining / follow-up

| ID | Priority | Item | Notes |
| --- | --- | --- | --- |
| TD-1 | Low | Dual SSE + Streamable HTTP maintenance | Legacy `/sse` mounts kept for transition; remove when ecosystem drops SSE-only clients. [PYPOST-653](https://pypost.atlassian.net/browse/PYPOST-653) |
| TD-2 | Low | `HTTPClient` SSE probe uses `"/sse" in url` heuristic | Resolved in [PYPOST-430](https://pypost.atlassian.net/browse/PYPOST-430); heuristic removed. |
| TD-3 | Low | `MCPClientService.run` uses `asyncio.run` | Pre-existing (PYPOST-368); `anyio.run` may be more reliable with SDK task groups. [PYPOST-560](https://pypost.atlassian.net/browse/PYPOST-560) |
| TD-4 | Low | User-facing `doc/mcp_integration.md` still describes SSE URL | [PYPOST-578](https://pypost.atlassian.net/browse/PYPOST-578) |
| TD-5 | Low | `config/test/README.md` example URLs still reference `/sse` | Update when refreshing test collection examples. [PYPOST-654](https://pypost.atlassian.net/browse/PYPOST-654) |

## Worklog

role: execution, step: 6, step_name: Tech Debt, tokens_used: (subagent aggregate)
