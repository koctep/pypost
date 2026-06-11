# PYPOST-549: Technical Debt (Step 6)

## Resolved under this epic (via child stories)

| Story | Outcome |
| --- | --- |
| [PYPOST-550](https://pypost.atlassian.net/browse/PYPOST-550) | Active environment variables injected into MCP `call_tool` |
| [PYPOST-551](https://pypost.atlassian.net/browse/PYPOST-551) | Streamable HTTP at `/mcp`; in-app client and tests migrated |

## Open child stories (epic not closable until Done)

| Key | Summary | Status |
| --- | --- | --- |
| PYPOST-552 | E2E Cursor verify + update `doc/mcp_integration.md` | To Do |
| PYPOST-553 | Tool metadata authoring | To Do |
| PYPOST-554 | Secrets / hidden vars policy | To Do |
| PYPOST-555 | UI preview of tool contract | To Do |
| PYPOST-556 | MCP overview + reliable server status | To Do |
| PYPOST-557 | Structured tool call result | To Do |
| PYPOST-561 | Prometheus in user-facing docs | To Do |
| PYPOST-562 | Extended MCP Prometheus metrics | To Do |

## Cross-cutting follow-ups (from completed children)

| ID | Priority | Item | Jira / owner |
| --- | --- | --- | --- |
| TD-1 | Low | Dual SSE + Streamable HTTP maintenance | PYPOST-551 — remove legacy `/sse` when ecosystem allows |
| TD-2 | Low | User-facing `doc/mcp_integration.md` still SSE URLs | [PYPOST-552](https://pypost.atlassian.net/browse/PYPOST-552) |
| TD-3 | Low | `HTTPClient` SSE URL heuristic | Pre-existing debt (PYPOST-430) |
| TD-4 | Low | Hardcoded legacy route paths in `MCPServerImpl` | [PYPOST-152](https://pypost.atlassian.net/browse/PYPOST-152) |
| TD-5 | Low | Port-busy error UX | [PYPOST-154](https://pypost.atlassian.net/browse/PYPOST-154), PYPOST-556 |

## Blocker review

**Verdict: NOT SAFE TO CLOSE EPIC** — six core stories (552–557) and observability stories
(561–562) remain open. Epic documentation and README vision alignment are complete; closure
waits on child story delivery.

## Worklog

role: execution, step: 6, step_name: Tech Debt, tokens_used: (subagent aggregate)
