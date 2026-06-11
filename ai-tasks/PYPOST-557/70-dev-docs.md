# PYPOST-557: Dev Docs Update

## Summary

Documented structured MCP tool call results for developers. Updated `doc/dev/mcp_integration.md`
with envelope schema, examples, protocol vs execution error separation, and API references.

## Files Updated

| File | Action |
| ---- | ------ |
| `doc/dev/mcp_integration.md` | Added PYPOST-557 section, tool execution step 7, API helpers |

## Documentation Highlights

### Envelope

JSON in `TextContent.text` with `status`, `error`, `body`, optional `logs`,
`error_category`, `error_message`.

### Error semantics

- `error: false` — HTTP call completed (including upstream 4xx/5xx).
- `error: true` — PyPost execution failure (`execution_error` or `status == 0`).
- Protocol errors — not JSON (unknown tool raises; internal exception plain text).

### Public helpers

- `format_structured_tool_result(result)` — serialize envelope.
- `_tool_result_has_error(result)` — internal flag logic (tested via unit tests).

## Tests (reference)

- `tests/test_mcp_server_impl.py` — `TestStructuredToolResultHelpers`, updated call_tool tests
- `tests/test_mcp_server_integration.py` — live round-trip JSON parsing

## Worklog

role: execution, step: 7, step_name: Dev Docs, tokens_used: (subagent)
