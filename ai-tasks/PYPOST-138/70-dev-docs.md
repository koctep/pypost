# PYPOST-138: Developer Documentation

## Summary

Documented that MCP tool execution creates a fresh `RequestService` (and `HTTPClient`) per
`call_tool` so threadpool workers never share a `requests.Session`.

## Files Updated

| File | Action |
| --- | --- |
| `doc/dev/mcp_integration.md` | Execution bullet + tool execution flow step 5 |

## Key contract

- `MCPServerImpl._create_request_service()` is the extension point for tests (stub the
  factory, not a removed `request_service` attribute).
- GUI sends remain one `RequestWorker` → one `RequestService` per click; MCP mirrors that
  one-shot pattern per tool invocation.

## Tests (reference)

- `tests/test_mcp_server_impl.py::test_execute_request_sync_creates_fresh_request_service_per_call`
