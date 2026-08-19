# Architecture: PYPOST-1090

## Detailed Documentation Plan

1. **`pypost/core/mcp_server_impl.py`**:
   Add clarifying comment above `McpSecretsPolicy.safe_execution_log_fields` in `_build_execution_variables`:
   ```python
   # Note: mcp_arg_count reflects the total post-default-injection argument count (len(merged_args));
   # the raw caller-supplied count can be recovered via (mcp_arg_count - defaults_applied_count).
   ```

2. **`doc/dev/mcp_integration.md`**:
   Update § Observability (lines 526-531 and 791-797) to document the field semantics as finalized.
