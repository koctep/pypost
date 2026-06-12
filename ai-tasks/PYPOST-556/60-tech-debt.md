# PYPOST-556: Technical Debt Analysis

## Shortcuts Taken

- **Starting state is UI-only** — no `MCPServerManager` signal for in-progress startup; label
  text is set in `EnvPresenter` before the listen signal arrives.

## Follow-ups

| ID | Priority | Item | Jira |
| --- | --- | --- | --- |
| TD-1 | Low | Auto-refresh overview when collections change without env switch | — | [PYPOST-661](https://pypost.atlassian.net/browse/PYPOST-661) |
| TD-2 | Low | Link overview rows to open request tab | — | [PYPOST-662](https://pypost.atlassian.net/browse/PYPOST-662) |
| TD-3 | Low | Metrics MCP server same reliable status pattern | [PYPOST-663](https://pypost.atlassian.net/browse/PYPOST-663) |

## Blocker review

**Verdict: SAFE TO CLOSE** — acceptance criteria met; follow-ups are enhancements.

## Worklog

role: execution, step: 6, step_name: Tech Debt, tokens_used: 1100
