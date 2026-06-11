# PYPOST-552: Technical Debt (Step 6)

## Resolved in this task

- User-facing `doc/mcp_integration.md` updated to Streamable HTTP `/mcp` (PYPOST-551 TD-4).
- `config/test/README.md` and List Tools URL in `examples/collections/mcp.json` (TD-5).
- Manual Cursor verification checklist added.
- Automated doc URL consistency tests added.

## Remaining / follow-up

| ID | Priority | Item | Notes |
| --- | --- | --- | --- |
| TD-1 | Low | Manual Cursor sign-off not in CI | Operator completes checklist; cannot automate desktop agent |
| TD-2 | Low | SSE probe tools still use `/sse` URLs | By design — HTTPClient SSE-probe heuristic (PYPOST-430) |
| TD-3 | Low | `doc/dev/architecture.md` metrics MCP line still mentions `/sse` | Minor; update in follow-up doc sweep |
| TD-4 | Low | PYPOST-578 duplicate scope | Close or link as duplicate of PYPOST-552 |

## Worklog

role: execution, step: 6, step_name: Tech Debt, tokens_used: 1200
