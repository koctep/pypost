# PYPOST-703: Redact MCP tool result response bodies

## Definition of Done

- MCP `call_tool` JSON envelope `body` is sanitized before agents receive it.
- Hidden environment values echoed in upstream responses are redacted to `***`.
- Common credential JSON fields, Bearer tokens, and sensitive query params are redacted.
- Post-script `logs` in the envelope use the same sanitization rules.
- Unit tests cover sanitizer and `call_tool` integration.
- `doc/dev/mcp_integration.md` documents agent-visible sanitization.

## Scope

**In scope:** `McpResponseSanitizer`, wiring in `format_structured_tool_result` / `call_tool`.

**Out of scope:** PYPOST-710 script log omission policy; collection-level MCP gates (PYPOST-711).
