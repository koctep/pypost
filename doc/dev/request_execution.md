# Request Execution Pipeline

## Overview

HTTP and MCP requests flow from the UI through `RequestWorker` into `RequestService.execute()`,
which coordinates transport, post-scripts, and history recording.

## Template rendering (PYPOST-410)

URL templates are rendered **once per HTTP request** inside `HTTPClient.send_request()`:

1. `render_string(request.url, variables)` resolves the URL (also used for SSE endpoint detection).
2. `_prepare_request_kwargs(..., rendered_url=url)` reuses that value for the actual request.

`RequestService.execute()` does **not** pre-render the URL. The former template render guard
was removed because it duplicated work without adding behavior beyond what the HTTP/MCP paths
already perform.

MCP requests render URL and body once each in `RequestService._execute_mcp()`.

History entries use `SensitiveDataMaskingPolicy` with resolved fields from transport
(PYPOST-63). Recording is orchestrated by private helpers (PYPOST-463):

1. `HTTPClient.send_request()` returns `HTTPRequestResult` with `resolved` (URL, headers, body).
2. `RequestService._record_execution_history()` delegates to:
   - `_build_history_entry()` — applies `build_history_safe_fields()` and constructs
     `HistoryEntry`
   - `_emit_history_masking_observability()` — pre-append debug log and masking metric
   - `HistoryManager.append()`
   - `_emit_history_entry_observability()` — post-append debug log and append metric
3. When **no hidden keys**, history reuses `resolved` without re-rendering.
4. When **hidden keys** are present, templates are re-rendered with `***` placeholders (masking
   requires a separate render pass).

## Error handling

Execution failures return `ExecutionResult` with `execution_error` set (PYPOST-400). Transport
layers raise `ExecutionError`; `execute()` catches and converts them to results.

Post-script failures populate `execution_error` with `ErrorCategory.SCRIPT` and the raw exception
string in `detail` (PYPOST-409). Callers such as `RequestWorker` and `MCPServerImpl` read
script errors from `execution_error` rather than a separate string field.

### Worker signals (PYPOST-412)

`RequestWorker.run()` does not catch `ExecutionError` from `execute()` — that path is
unreachable because `RequestService.execute()` always returns `ExecutionResult` for handled
failures.

| Signal | When emitted |
|--------|----------------|
| `finished` | Successful response or handled failure (`ExecutionResult` with synthetic error response) |
| `error` | Unexpected `Exception` in the worker thread, wrapped as `ErrorCategory.UNKNOWN` |
| `script_output` | Post-script logs; script failure detail from `execution_error` when category is `SCRIPT` |
| `retry_attempt` | Retry progress from `RequestService._execute_http_with_retry` |

### MCP transport exceptions (PYPOST-411)

`MCPClientService.run()` maps httpx exceptions from the MCP SSE client to `ExecutionError`:

| Exception | `ErrorCategory` |
|-----------|-----------------|
| `asyncio.TimeoutError` (outer `wait_for`) | `TIMEOUT` |
| `httpx.TimeoutException` | `TIMEOUT` |
| `httpx.NetworkError` (includes `ConnectError`) | `NETWORK` |
| `httpx.RequestError` (other transport) | `UNKNOWN` |
| Other `Exception` | `UNKNOWN` |

`httpx.TimeoutException` is caught before `httpx.NetworkError` because both inherit from
`httpx.TransportError` but are siblings, not parent/child.

## Key files

| File | Role |
|------|------|
| `pypost/core/worker.py` | Background thread; calls `RequestService.execute()` |
| `pypost/core/request_service.py` | Orchestrates MCP/HTTP, scripts, history |
| `pypost/core/http_client.py` | HTTP transport; single URL render per send |
| `pypost/core/mcp_client_service.py` | MCP transport; typed httpx error mapping |
| `pypost/core/template_service.py` | Jinja2 rendering and validation |

## Tests

- `tests/test_request_service.py` — `test_execute_http_does_not_pre_render_url`
- `tests/test_http_client.py` — `test_url_template_rendered_once_per_request`
- `tests/test_mcp_client_service.py` — httpx exception category mapping
