# PYPOST-557: Structured MCP tool call result

## Research

### Current behavior

`MCPServerImpl.call_tool` returns raw `result.response.body` as `TextContent`. Script logs and
script errors are appended as free-form sections (`--- Script Logs ---`, `--- Script Error ---`).
Metrics always record `"success"` on the execution path even when `execution_error` is set.

### Available data

`RequestService.execute()` returns `ExecutionResult`:

| Field | Use in envelope |
| --- | --- |
| `response.status_code` | `status` |
| `response.body` | `body` |
| `execution_error` | drives `error` flag + optional category/message |
| `script_logs` | optional `logs` array |

`ErrorCategory` values (`network`, `timeout`, `template`, `script`, …) map to
`error_category` string.

### Protocol vs execution errors

| Case | Behavior |
| --- | --- |
| Unknown tool | `raise ValueError` — MCP protocol error (unchanged) |
| `RequestService` failure | JSON envelope, `error: true` |
| Upstream HTTP 4xx/5xx | JSON envelope, `error: false`, real status |
| Unexpected exception in `call_tool` | Plain text `Error executing request: …` (protocol) |

## Implementation Plan

1. Add pure helpers in `mcp_server_impl.py`:
   - `_tool_result_has_error(result) -> bool`
   - `format_structured_tool_result(result) -> str` (JSON)
2. Replace body formatting in `call_tool` with `format_structured_tool_result`.
3. Set metrics outcome `"error"` when `_tool_result_has_error` else `"success"`.
4. Update `tests/test_mcp_server_impl.py` and `tests/test_mcp_server_integration.py`.
5. Document envelope in `doc/dev/mcp_integration.md`.

## Architecture

```mermaid
flowchart LR
    Agent[MCP client] -->|call_tool| Impl[MCPServerImpl]
    Impl --> RS[RequestService.execute]
    RS --> ER[ExecutionResult]
    ER --> Fmt[format_structured_tool_result]
    Fmt --> TC[TextContent JSON text]
    TC --> Agent
```

### Envelope schema

```json
{
  "status": 200,
  "error": false,
  "body": "...",
  "logs": ["line1"],
  "error_category": "network",
  "error_message": "Could not connect..."
}
```

- `logs`, `error_category`, `error_message` omitted when not applicable.

### Module changes

| Module | Change |
| --- | --- |
| `mcp_server_impl.py` | Format helpers; `call_tool` returns JSON text |
| `tests/test_mcp_server_impl.py` | Assert parsed JSON fields |
| `tests/test_mcp_server_integration.py` | Round-trip JSON parsing |
| `doc/dev/mcp_integration.md` | Document envelope and error semantics |

**Unchanged:** `RequestService`, `MCPServerManager`, UI, secrets policy.

## Q&A

| Question | Answer |
| --- | --- |
| Why JSON in TextContent? | MCP SDK tool results are text blocks; JSON keeps one content item. |
| Why not use MCP isError? | Envelope covers execution semantics; protocol errors stay separate. |
