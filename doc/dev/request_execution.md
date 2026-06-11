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

History entries use `SensitiveDataMaskingPolicy`, which renders templates again for masked
storage — independent of the transport hot path.

## Error handling

Execution failures return `ExecutionResult` with `execution_error` set (PYPOST-400). Transport
layers raise `ExecutionError`; `execute()` catches and converts them to results.

## Key files

| File | Role |
|------|------|
| `pypost/core/worker.py` | Background thread; calls `RequestService.execute()` |
| `pypost/core/request_service.py` | Orchestrates MCP/HTTP, scripts, history |
| `pypost/core/http_client.py` | HTTP transport; single URL render per send |
| `pypost/core/template_service.py` | Jinja2 rendering and validation |

## Tests

- `tests/test_request_service.py` — `test_execute_http_does_not_pre_render_url`
- `tests/test_http_client.py` — `test_url_template_rendered_once_per_request`
