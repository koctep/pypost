# PYPOST-560: Observability

## Scope

This ticket modifies `MCPClientService` which wraps async MCP client operations. It preserves all existing logging and error categories.

## Logging

- `MCPClientService` logs `mcp_operation_start` at debug level when starting an operation.
- Logs `mcp_operation_timeout` at error level if the operation times out (total timeout of 25.0s).
- Logs `mcp_operation_failed` at error level with the error category (e.g. `NETWORK`, `TIMEOUT`, `UNKNOWN`) and detail if any other exception occurs.
- Logs `mcp_operation_success` at debug level with the elapsed time on successful completion.

## Error Categories

The error categories mapped to `ExecutionError` remain unchanged:
- `TimeoutError` / `httpx.TimeoutException` -> `ErrorCategory.TIMEOUT`
- `httpx.NetworkError` -> `ErrorCategory.NETWORK`
- `httpx.RequestError` / other exceptions -> `ErrorCategory.UNKNOWN`
