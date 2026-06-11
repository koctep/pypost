# PYPOST-411: Observability

## Impact

No new log lines or metrics. Existing structured logging preserved with the same event keys.

## Logging

| Event key | Level | When |
|-----------|-------|------|
| `mcp_operation_timeout` | ERROR | Outer `asyncio.wait_for` timeout |
| `mcp_operation_failed` | ERROR | httpx or fallback exception with `category` field |
| `mcp_operation_success` | DEBUG | Successful MCP operation |

The `category` field in `mcp_operation_failed` now reflects the typed `ErrorCategory` value
from explicit exception handling rather than heuristic classification.

## Metrics

Unchanged. `RequestService` still calls `track_request_error(category)` when catching
`ExecutionError` from `MCPClientService`.

## Verification

- `test_connect_error_raises_execution_error_network` — NETWORK category
- `test_read_timeout_raises_execution_error_timeout` — TIMEOUT via httpx
- `test_timeout_raises_execution_error_timeout` — TIMEOUT via asyncio
- `test_unknown_error_raises_execution_error_unknown` — UNKNOWN fallback
