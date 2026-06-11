# PYPOST-554: Technical Debt

## Non-blockers

| Item | Notes | Follow-up |
| --- | --- | --- |
| MCP response body may contain secrets from upstream API | Out of scope; agent sees HTTP response as today | PYPOST-557 |
| Tool contract preview UI | Policy ready; preview should reuse `McpSecretsPolicy` | PYPOST-555 |
| `mcp_description` is user-authored free text | Operator responsibility; no auto-redaction | Document in user guide |
| Env var named `mcp` vs namespace collision | Documented in PYPOST-550 | None |

## Blockers

None — safe to close after tests pass.
