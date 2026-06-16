# PYPOST-703: MCP response sanitization architecture

## Design

Add `McpResponseSanitizer` in `pypost/core/mcp_response_sanitizer.py`:

1. Replace literal hidden env values (longest-first) with `HIDDEN_PLACEHOLDER`.
2. Parse JSON bodies and redact keys matching sensitive name heuristics.
3. Redact `Bearer …` tokens and `?token=` / `&api_key=` query values in plain text.

`format_structured_tool_result` accepts `env_vars` and `hidden_keys`; `call_tool` passes
suppliers already used for schema filtering.

## Flow

```
call_tool → execute → format_structured_tool_result(result, env, hidden)
                              → McpResponseSanitizer.sanitize_body / sanitize_logs
                              → TextContent JSON
```
