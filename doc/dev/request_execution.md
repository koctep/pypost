# Request Execution Pipeline

## Overview

HTTP and MCP requests flow from the UI through `RequestWorker` into `RequestService.execute()`,
which coordinates transport, post-scripts, and history recording.

## Template rendering (PYPOST-410)

URL templates are rendered **once per HTTP request** inside `HTTPClient.send_request()`:

1. `render_string(request.url, variables)` resolves the URL once per send.
2. `_prepare_request_kwargs(..., rendered_url=url)` reuses that value for the actual request.

**SSE stream handling (PYPOST-430):** After the response arrives, GET requests with
`Content-Type: text/event-stream` are routed to SSE probe parsing (`_handle_sse_response`).
URL path is not used for detection. When the request already includes
`Accept: text/event-stream`, `HTTPClient` applies shorter SSE probe connect/read timeouts
before dispatch.

`RequestService.execute()` does **not** pre-render the URL. The former template render guard
was removed because it duplicated work without adding behavior beyond what the HTTP/MCP paths
already perform.

MCP requests render URL, headers, and body in `RequestService._execute_mcp()`.
Resolved headers are forwarded to `MCPClientService.run` (PYPOST-1173).

**Inbound MCP tools (PYPOST-550):** When an external agent calls `call_tool`, `MCPServerImpl`
merges the configured endpoint environment's snapshot with `mcp.request` tool arguments before
calling `RequestService.execute()`. Template rendering and HTTP execution then follow the same
path as GUI sends. See [Multiple MCP Servers](mcp_server_registry.md).

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

### History recording by entry point (PYPOST-701)

Not every caller of `RequestService.execute()` records history. History requires an injected
`HistoryManager`; when `history_manager` is `None`, `_record_execution_history()` is a no-op.

| Entry point | `history_manager` | Records history |
| --- | --- | --- |
| GUI (`RequestWorker` via `TabsPresenter`) | Composition-root `HistoryManager` | Yes |
| Inbound MCP (`MCPServerImpl._create_request_service`) | Omitted (per-call instance) | No |
| Outbound MCP request (user sends MCP tab) | Same as GUI when worker has manager | Yes |

**Product choice:** Inbound MCP asymmetry is intentional (audit R-P3-003). Session-scoped MCP
activity telemetry lives in `McpActivityDialog` (PYPOST-141), not the history file. See
[History asymmetry (product choice)](mcp_integration.md#history-asymmetry-product-choice-pypost-701)
in `mcp_integration.md`.

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

### Response body streaming display (PYPOST-887)

`RequestWorker` may emit `chunk_received` while the body is still streaming. The presenter
debounces those chunks (~33 ms) into `ResponseView.append_body`, then on `finished` calls
`display_response` (`setText` of the full body). Pending flush state is discarded on
finish, error, and re-send so a late timer cannot double the body.

See [Response Streaming Display](response-streaming-display.md).

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

### Save handler tab binding (PYPOST-162)

`_create_request_tab` is the single production path for new request tabs. It applies indent,
environment, and template setup, then calls `_wire_tab_signals`.

Save and save-as use the same closure pattern as send:

```python
tab.request_editor.save_requested.connect(
    lambda data, t=tab: self._handle_save_request(t, data)
)
tab.request_editor.save_as_requested.connect(
    lambda data, t=tab: self._handle_save_as_request(t, data)
)
```

`_handle_save_request(source_tab, request_data)` and `_handle_save_as_request(source_tab,
request_data)` use the captured tab directly. `_find_tab_for_sender` was removed; post-dialog
`currentIndex()` fallbacks are no longer needed.

### MCP transport exceptions (PYPOST-411)

`MCPClientService.run()` accepts optional `headers` and passes them to
`create_mcp_http_client`. It maps httpx exceptions from the MCP SSE client to
`ExecutionError`:

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
