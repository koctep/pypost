# PYPOST-554: Observability

## Logging

| Event | Level | Fields | Notes |
| --- | --- | --- | --- |
| `mcp_execution_variables_merged` | DEBUG | `env_var_count`, `hidden_key_count`, `mcp_arg_count` | Counts only — no names or values |

## Metrics

No new metrics. Existing MCP request/response counters unchanged.

## Security

Policy ensures DEBUG diagnostics never include hidden variable names or values. Aligns with
PYPOST-550 observability and PYPOST-446 history masking goals.
