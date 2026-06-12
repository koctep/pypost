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

**Inbound MCP tools (PYPOST-550):** When an external agent calls `call_tool`, `MCPServerImpl`
merges the active environment's variables with `mcp.request` tool arguments before calling
`RequestService.execute()`. Template rendering and HTTP execution then follow the same path as
GUI sends. See [MCP Integration](mcp_integration.md#environment-variable-injection-pypost-550).

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

### Worker signals (PYPOST-412, PYPOST-413)

`RequestWorker.run()` does not catch `ExecutionError` from `execute()` — that path is
unreachable because `RequestService.execute()` always returns `ExecutionResult` for handled
failures.

| Signal | When emitted |
|--------|----------------|
| `finished` | Successful response or handled failure (`ExecutionResult` with synthetic error response) |
| `error` | User cancellation (`ErrorCategory.CANCELLED`) or unexpected `Exception` wrapped as `UNKNOWN` |
| `script_output` | Post-script logs; script failure detail from `execution_error` when category is `SCRIPT` |
| `retry_attempt` | Retry progress from `RequestService._execute_http_with_retry` |

### Request cancellation (PYPOST-413)

When `stop_flag()` is set (user clicks Stop), `RequestService._execute_http_with_retry`
raises `ExecutionError(category=CANCELLED, ...)`. `execute()` returns an `ExecutionResult`
but does **not** increment `request_errors_total`.

`RequestWorker` emits `error` (not `finished`) for `CANCELLED` results. `TabsPresenter.
_on_request_error` checks `error.category == ErrorCategory.CANCELLED` and returns without
showing a dialog. Legacy `str` cancellation payloads still use substring matching.

### Tab worker lifecycle (PYPOST-401, PYPOST-415)

Each tab holds at most one active `RequestWorker` in `tab.worker`. Cleanup is centralized in
`TabsPresenter._clear_tab_worker()`:

| Call site | When |
|-----------|------|
| `_on_request_finished` / `_on_request_error` | Normal completion path (before UI reset) |
| `_handle_send_request` stale guard | Worker finished but Qt has not yet delivered the handler |

`_reset_tab_ui_state()` only restores the Send button; it does not touch `tab.worker`.

Because `finished`/`error` signals are queued on the Qt event loop, `tab.worker` may still
reference a dead thread briefly after `isRunning()` becomes `False`. The stale guard clears
that reference when the user sends again before the completion handler runs.

Debug log `stale_worker_cleared` indicates the guard fired (see PYPOST-401 observability).

### One-shot worker instances (PYPOST-417)

`RequestWorker` is **not reusable** after `stop()`. The cooperative cancel flag
(`threading.Event`) is cleared only in `__init__` and set by `stop()`; it is never reset in
`run()`. Calling `start()` again on a stopped instance would run with `stop_flag()` always
true, silently cancelling the new request.

**Contract:** one `RequestWorker` per send. `TabsPresenter._handle_send_request` always
constructs a new worker; completion handlers clear `tab.worker` via `_clear_tab_worker()`.

### Send handler tab binding (PYPOST-71)

`_wire_tab_signals` connects `send_requested` with a closure that captures the `RequestTab`:

```python
tab.request_editor.send_requested.connect(
    lambda data, t=tab: self._handle_send_request(t, data)
)
```

`_handle_send_request(sender_tab, request_data)` uses that reference directly and does not call
`QObject.sender()`, so the handler works outside a signal-slot context (e.g. unit tests).

See `tests/test_worker_race.py::test_worker_not_reusable_after_stop`.

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
- `tests/test_worker_race.py` — worker stop flag and tab worker lifecycle guards
