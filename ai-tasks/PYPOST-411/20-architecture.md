# PYPOST-411: Architecture

## Current state (before)

```python
except Exception as exc:
    err_type = type(exc).__name__
    if "ConnectError" in err_type or "connection" in err_msg.lower():
        category = ErrorCategory.NETWORK
    elif "Timeout" in err_type or "timeout" in err_msg.lower():
        category = ErrorCategory.TIMEOUT
    else:
        category = ErrorCategory.UNKNOWN
```

Classification depends on substring matching in type names and messages.

## Target state (after)

Explicit `except` chain ordered by httpx exception hierarchy (most specific first):

| Exception | `ErrorCategory` | Message |
|-----------|-----------------|---------|
| `asyncio.TimeoutError` | `TIMEOUT` | MCP request timed out after {N}s |
| `httpx.TimeoutException` | `TIMEOUT` | MCP server did not respond in time |
| `httpx.NetworkError` | `NETWORK` | Could not connect to MCP server |
| `httpx.RequestError` | `UNKNOWN` | MCP operation failed |
| `Exception` (fallback) | `UNKNOWN` | MCP operation failed |

`httpx.NetworkError` is a superclass of `ConnectError`, `ReadError`, and `WriteError`.
`httpx.TimeoutException` covers `ConnectTimeout`, `ReadTimeout`, `WriteTimeout`, and
`PoolTimeout`.

## Change sites

| File | Change |
|------|--------|
| `pypost/core/mcp_client_service.py` | Import `httpx`; replace heuristic `except Exception` with typed clauses |
| `tests/test_mcp_client_service.py` | Use `httpx.ConnectError` / `httpx.ReadTimeout` in error tests |
| `doc/dev/request_execution.md` | Document MCP exception mapping |

## Unchanged

- Success path returns `ResponseData` with `status_code=200`.
- `RequestService._execute_mcp()` catch-and-convert pattern unchanged.
- Logging keys (`mcp_operation_timeout`, `mcp_operation_failed`) unchanged.

## Data flow

```
MCPClientService.run()
  └─ asyncio.wait_for(_run_async(), MCP_TOTAL_TIMEOUT)
       ├─ asyncio.TimeoutError ──────────────► ExecutionError(TIMEOUT)
       └─ _run_async() via sse_client (httpx)
            ├─ httpx.TimeoutException ───────► ExecutionError(TIMEOUT)
            ├─ httpx.NetworkError ───────────► ExecutionError(NETWORK)
            ├─ httpx.RequestError ───────────► ExecutionError(UNKNOWN)
            └─ other Exception ──────────────► ExecutionError(UNKNOWN)
```
