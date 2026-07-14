# PYPOST-681: Architecture

## Change

Extend `format_structured_tool_result` in `pypost/core/mcp_server_impl.py`:

```
ExecutionResult.execution_error.detail set?
  yes → payload["error_detail"] = McpResponseSanitizer.sanitize_text(detail, env, hidden)
  no  → omit key
```

## Design notes

- Reuse existing `env_vars` / `hidden_keys` passed into `format_structured_tool_result`.
- `error_message` remains the short human-readable summary; `error_detail` carries technical text.
- No API or transport changes — agents already parse JSON from `TextContent.text`.
