# PYPOST-366: Architecture

## Current State (post PYPOST-554)

MCP variable extraction split into two policy methods in `pypost/core/mcp_secrets_policy.py`:

| Method | Purpose | Mechanism |
| --- | --- | --- |
| `extract_mcp_request_variables` | Agent tool inputs (`mcp.request.*`) | Regex `_MCP_REQUEST_VAR_PATTERN` over url/body/headers/params |
| `extract_environment_variable_names` | Env-resolved placeholders | Jinja2 AST via `template_service.parse` + `meta.find_undeclared_variables` |

`MCPServerImpl._generate_schema` and `mcp_tool_contract.build_mcp_tool_contract_preview` call
the policy methods — `_extract_mcp_variables` was removed from `mcp_server_impl.py`.

## Change Plan

No behavioral change required. Task validates PYPOST-38 tech-debt resolution:

1. Confirm `extract_mcp_request_variables` has **no** Jinja2 AST branch (regex only).
2. Confirm `_extract_mcp_variables` is absent from `mcp_server_impl.py`.
3. Update `doc/dev/mcp_integration.md` schema generation overview to name current functions.

## Data Flow (unchanged)

```
RequestData fields
    → extract_mcp_request_variables (regex)
    → resolve_mcp_param_specs
    → filter_agent_param_specs (uses env-name extraction separately)
    → build_tool_input_schema
```

## Out of Scope

- Changing regex semantics or env-variable AST extraction.
- PYPOST-367..372 follow-ups (separate issues).
