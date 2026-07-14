# PYPOST-681: Add optional error_detail to MCP error envelope

## Definition of Done

- MCP JSON envelope includes optional `error_detail` when `ExecutionError.detail` is set.
- `error_detail` is omitted when `detail` is `None`.
- Value is sanitized via `McpResponseSanitizer` (same rules as `body` and `logs`).
- Unit tests cover inclusion, omission, and secret redaction.
- `doc/dev/mcp_integration.md` documents the new field.

## Scope

**In scope:** `format_structured_tool_result`, tests, developer docs.

**Out of scope:** Changing `error_message` semantics; protocol-level MCP errors.

## Acceptance Criteria

| ID | Criterion |
| --- | --- |
| AC-1 | `error_detail` present in envelope when `execution_error.detail` is not `None` |
| AC-2 | `error_detail` absent when `detail` is `None` |
| AC-3 | Hidden env values in `detail` are redacted to `***` |
| AC-4 | Field documented in `doc/dev/mcp_integration.md` |
