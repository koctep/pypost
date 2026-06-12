# PYPOST-136: Technical Debt Review

## Blockers

None — implementation meets acceptance criteria.

## Non-blockers / Follow-ups

| Item | Severity | Notes |
| --- | --- | --- |
| In-flight client sessions | Low | Restart drops active MCP sessions; clients reconnect and re-list tools. Acceptable for local dev server. |
| Hot reload without restart | Low | Would need MCP SDK support for dynamic handler registration; restart is sufficient for now. |
| `expose_as_mcp` toggle off mid-session | Low | Signature change triggers restart; agent may still hold cached tool names until reconnect. | [PYPOST-587](https://pypost.atlassian.net/browse/PYPOST-587) |

## Resolved from PYPOST-16

- **Restart on Update** — addressed by this task.

## Worklog

role: review, step: 6, step_name: Tech Debt, tokens_used: 1100
