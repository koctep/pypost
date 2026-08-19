# Observability: PYPOST-1090

## Overview

Audited observability documentation for `mcp_execution_variables_merged`.

## Findings

- `mcp_execution_variables_merged` emits `env_var_count`, `hidden_key_count`, `mcp_arg_count`, and `defaults_applied_count`.
- `mcp_arg_count` reflects the count of arguments after default injection (`len(merged_args)`).
- The raw argument count is recoverable via `(mcp_arg_count - defaults_applied_count)`.
- Documented in `pypost/core/mcp_server_impl.py` and `doc/dev/mcp_integration.md`.
