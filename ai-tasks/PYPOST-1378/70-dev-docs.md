# PYPOST-1378: Developer Documentation

## Overview

PYPOST-1378 (MASK-2) implements permanent, fail-closed MCP output masking for requests configured with `hidden_response_fields`. When an AI coding agent executes an HTTP request exposed as an MCP tool, sensitive fields (passwords, tokens, secrets, PII) are permanently masked with `***` before serialization across the MCP protocol.

This ensures external LLMs and automated agents never receive raw credentials, establishing an irreversible security boundary with zero reveal parameters or auxiliary reveal tools exposed in MCP schemas.

---

## Documentation Updated

1. **`doc/dev/hidden_response_fields.md`**:
   - Updated Section 2 with complete MASK-2 permanent MCP response masking architecture.
   - Documented `McpResponseSanitizer` and `redact_json_response_fields` integration into `format_structured_tool_result`.
   - Documented irreversible security boundary invariant (zero reveal parameters, zero reveal tools, no reveal bypass).
   - Documented selector syntax support: simple/root keys, dot-notation paths, array wildcards, header selectors (`header:` prefix).
   - Documented non-JSON pass-through and graceful error fallback behavior.
   - Documented display-only immutability of underlying in-memory `ResponseData` and execution history.
   - Documented telemetry metric (`hidden_value_masks_applied_total{surface="mcp"}`) and structured zero-leakage debug logging.

2. **`doc/dev/mcp.md`**:
   - Created developer reference documentation for PyPost's MCP subsystem and security guarantees.
   - Detailed fail-closed response field masking guarantees for MCP client agents.
   - Documented tool execution lifecycle, sanitization pipelines, and schema reflection security boundaries.
   - Summarized observability metrics, structured logging rules, and operator verification procedures.

---

## Architecture & Implementation Summary

- **Pipeline Integration**:
  - `pypost/core/sensitive_text_sanitizer.py`:
    - Added `redact_json_response_fields(body, hidden_fields, placeholder="***")` supporting recursive tree traversal and path matching.
    - Added `_format_path_variants` evaluating simple key, full dot-notation, array wildcard (`[*]`), and shorthand dot-notation.
    - Updated `sanitize_headers` to respect `header:<Name>` selectors from `hidden_response_fields`.
  - `pypost/core/mcp_response_sanitizer.py`:
    - Updated `McpResponseSanitizer.sanitize_body` to coordinate `redact_json_response_fields` and `sanitize_text`.
  - `pypost/core/mcp_server_impl.py`:
    - Updated `format_structured_tool_result` to accept and pass `hidden_response_fields` to `McpResponseSanitizer.sanitize_body`.
    - Updated `MCPServerImpl._call_tool_inner` to extract `item.hidden_response_fields` from `RequestData` and increment `hidden_value_masks_applied_total` (`surface="mcp"`).
- **Security Boundary**:
  - Zero unmask parameters in `mcp_tool_contract.build_tool_input_schema`.
  - Zero reveal tools registered in `MCPServerImpl`.
  - Raw in-memory `ResponseData` on `ExecutionResult` and history storage remain authentic.

---

## Verification Instructions

All verification must be executed exclusively through repository `make` targets:

```bash
# Run fast test suite for MCP hidden response fields masking
make test PYTEST_ARGS="tests/test_mcp_hidden_response_fields_masking.py"

# Run flake8 static analysis and doc linting
make lint

# Run static type checking
make typecheck

# Verify integrity of AI task artifacts
make verify-ai-tasks

# Run combined quality gate
make check
```
