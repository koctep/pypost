# PYPOST-77: Architecture

## Current State (post PYPOST-554)

MCP request-variable extraction lives in `pypost/core/mcp_secrets_policy.py`:

| Element | Location | Notes |
| --- | --- | --- |
| `import re` | Module level (line 5) | PEP 8 compliant |
| `_MCP_REQUEST_VAR_PATTERN` | Module level (lines 13–15) | Compiled once at import |
| `extract_mcp_request_variables` | `McpSecretsPolicy` static method | Uses module-level pattern |

`MCPServerImpl` no longer contains `_extract_mcp_variables` or any inline `import re`.

## Change Plan

No behavioral change required. Task validates TD-5 resolution:

1. Confirm `import re` is at module top in `mcp_secrets_policy.py`.
2. Confirm `_MCP_REQUEST_VAR_PATTERN` is module-level (not recompiled per call).
3. Confirm `mcp_server_impl.py` has no function-scoped `import re`.
4. Update `doc/dev/mcp_secrets_policy.md` to document regex extraction API.

## Data Flow (unchanged)

```
RequestData fields
    → extract_mcp_request_variables (regex via _MCP_REQUEST_VAR_PATTERN)
    → resolve_mcp_param_specs
    → filter_agent_param_specs
    → build_tool_input_schema
```

## Out of Scope

- TD-4 dead Jinja2 branch — closed in PYPOST-76.
- Changing regex semantics or env-variable AST extraction.
