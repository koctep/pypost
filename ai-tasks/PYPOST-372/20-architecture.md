# PYPOST-372: Architecture

## Current State (verified)

MCP variable extraction lives in `pypost/core/mcp_secrets_policy.py`:

| Method | Purpose | Mechanism |
| --- | --- | --- |
| `extract_mcp_request_variables` | Agent tool inputs (`mcp.request.*`) | Regex `_MCP_REQUEST_VAR_PATTERN` only |
| `extract_environment_variable_names` | Env-resolved placeholders | Jinja2 AST (live path — not dead code) |

`MCPServerImpl` no longer defines `_extract_mcp_variables`; schema generation delegates to
policy methods and `mcp_tool_contract` helpers (PYPOST-554).

## Verification Plan

1. Grep `mcp_server_impl.py` — confirm `_extract_mcp_variables` absent.
2. Read `extract_mcp_request_variables` — confirm no Jinja2 AST branch.
3. Run MCP secrets-policy tests to confirm behavior unchanged.

## Outcome

All checks pass. No architecture change required for this task.

## Relation to PYPOST-366

PYPOST-366 performed the same verification and updated `doc/dev/mcp_integration.md`. PYPOST-372
closes the duplicate PYPOST-38 follow-up link with ai-tasks documentation only.
