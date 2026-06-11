# PYPOST-549: Dev Docs (Step 7)

Epic scope: coordinate documentation; **no new `doc/dev/` files required** for the epic
ticket itself. Developer detail lives in existing modules and child-story updates.

## Canonical references

| Document | Purpose | Epic alignment |
| --- | --- | --- |
| [README.md](../../README.md) Vision | Product vision — matches Jira epic | Verified Step 3 |
| [doc/dev/mcp_integration.md](../../doc/dev/mcp_integration.md) | Architecture, `/mcp` URLs, components | Updated by PYPOST-551; primary dev reference |
| [doc/dev/testing.md](../../doc/dev/testing.md) | MCP integration test setup, `/mcp` URL | Updated by PYPOST-551 |
| [doc/mcp_integration.md](../../doc/mcp_integration.md) | User-facing setup (Cursor, Claude) | **Out of date** — SSE URLs; [PYPOST-552](https://pypost.atlassian.net/browse/PYPOST-552) |

## Step 3: README verification

Compared README Vision to Jira epic PYPOST-549:

| Epic element | README |
| --- | --- |
| Vision one-liner | Matches |
| North star | Matches |
| Principles (safety, reuse, local-first) | Matches; README adds operator/agent split and Prometheus |
| Scope (one request = one tool, local network MCP) | Implied by features; not repeated verbatim — acceptable |
| Streamable HTTP `/mcp` URL | Not in Vision section (no `/sse` either) — no README edit |

**Action:** README unchanged. User-facing transport URLs updated in PYPOST-552
(`doc/mcp_integration.md`), not in epic Step 3.

## Child story dev-doc artifacts

- `ai-tasks/PYPOST-550/70-dev-docs.md`
- `ai-tasks/PYPOST-551/00-roadmap.md` (Step 7: `doc/dev/mcp_integration.md`, `doc/dev/testing.md`)

## Worklog

role: execution, step: 7, step_name: Dev Docs, tokens_used: (subagent aggregate)
