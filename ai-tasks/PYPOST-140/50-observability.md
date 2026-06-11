# PYPOST-140: Observability

## Existing signals (unchanged)

MCP tool argument support reuses observability from PYPOST-550 and PYPOST-554:

| Signal | Scope | Notes |
| --- | --- | --- |
| `mcp_execution_variables_merged` (DEBUG) | Each `call_tool` | Logs `env_var_count`, `hidden_key_count`, `mcp_arg_count` — no names or values |
| `mcp_requests_total` / `mcp_responses_total` | Per tool method | Tracks inbound calls and success/error outcomes |
| `McpActivityEntry.new_call_tool` | Activity log | Records `mcp_arg_count` without argument values (PYPOST-141) |

## Verification

Argument merge logging confirms agents supplied parameters reach execution without exposing
secret values. No additional metrics or logging required for PYPOST-140 closure.
