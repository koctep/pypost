# PYPOST-400: Developer Documentation

## Overview

PYPOST-400 introduces structured error handling across the post publishing flow. Before this
change, errors propagated as raw exceptions or plain strings with no consistent contract between
layers. After this change, every failure is represented by an `ExecutionError` with a typed
`ErrorCategory`, a human-readable message, and an optional technical detail string.

---

## New Module: `pypost/models/errors.py`

### `ErrorCategory`

```python
class ErrorCategory(str, enum.Enum):
    NETWORK  = "network"   # DNS / connection refused / host unreachable
    TIMEOUT  = "timeout"   # Request or MCP operation exceeded timeout
    TEMPLATE = "template"  # Jinja2 template rendering failure
    SCRIPT   = "script"    # Post-request script execution failure
    HISTORY  = "history"   # History recording failure (non-fatal)
    UNKNOWN  = "unknown"   # Uncategorized exception
```

Using `str` as a mixin means `ErrorCategory.NETWORK == "network"` is `True`. This lets values
be passed directly as Prometheus label strings without calling `.value`.

### `ExecutionError`

```python
@dataclass
class ExecutionError(Exception):
    category: ErrorCategory
    message: str            # Human-readable, actionable — shown in UI
    detail: Optional[str]   # Raw exception string — logs and debug view only
```

`ExecutionError` is both an `Exception` (so it can be raised) and a dataclass (so it can be
stored in `ExecutionResult.execution_error`). `__str__` returns `message`, keeping log lines
readable.

---

## Error Flow by Layer

### `HTTPClient` (`pypost/core/http_client.py`)

Catches `requests` exceptions and raises typed `ExecutionError`:

| `requests` exception | `ErrorCategory` |
|----------------------|-----------------|
| `requests.Timeout` | `TIMEOUT` |
| `requests.ConnectionError` | `NETWORK` |
| `requests.RequestException` (other) | `UNKNOWN` |

`requests.Timeout` is caught before `requests.ConnectionError` because it is a subclass of
`ConnectionError` in some `requests` versions.

### `MCPClientService` (`pypost/core/mcp_client_service.py`)

Catches async MCP exceptions and raises typed `ExecutionError`:

| Condition | `ErrorCategory` |
|-----------|-----------------|
| `asyncio.TimeoutError` (outer `wait_for`) | `TIMEOUT` |
| `ConnectError` in type name or `"connection"` in message | `NETWORK` |
| `Timeout` in type name or `"timeout"` in message | `TIMEOUT` |
| Anything else | `UNKNOWN` |

On success, returns a `ResponseData` with `status_code=200`.

### `RequestService` (`pypost/core/request_service.py`)

`execute()` is the single entry point for all request execution. It **never raises** — it always
returns an `ExecutionResult`.

Error handling inside `execute()`:

1. **Template render guard** (before HTTP dispatch) — wraps `TemplateService.render_string()`;
   on failure raises `ExecutionError(TEMPLATE)`.
2. **HTTP/MCP execution block** — catches `ExecutionError` from `HTTPClient` or
   `MCPClientService`, calls `MetricsManager.track_request_error(category)`, and returns an
   `ExecutionResult` with a synthetic `ResponseData` (status 0) and `execution_error` set.
3. **Script error** — wraps `ScriptExecutor` string error into
   `ExecutionError(SCRIPT)` stored in `execution_error`.
4. **History failure** — non-fatal; calls `MetricsManager.track_history_record_error()` and
   logs at `ERROR` level but does not affect the returned result.

`ExecutionResult` fields relevant to errors:

```python
@dataclass
class ExecutionResult:
    response: ResponseData            # status_code=0 on failure, real code on success
    updated_variables: Dict[str, Any]
    script_logs: List[str]
    script_error: Optional[str]       # Legacy string field; kept for backward compatibility
    execution_error: Optional[ExecutionError] = None  # Structured error; None on success
```

### `RequestWorker` (`pypost/core/worker.py`)

The `error` signal is `Signal(object)`. Its payload is:

- `ExecutionError` — for all real failures (the normal case after this change)
- `str` — reserved for the cancellation/stop path (legacy, may be removed in a future sprint)

The worker calls `RequestService.execute()`, which never raises (except for the template guard).
Both `except ExecutionError` and `except Exception` handlers in `RequestWorker.run()` exist as a
safety net and to wrap truly unexpected exceptions.

### `tabs_presenter.py` (`pypost/ui/presenters/tabs_presenter.py`)

`_on_request_error(tab, error)` handles both payload types:

- `str` payload → legacy path; cancellation strings are silently ignored; all others show
  `QMessageBox.critical("Error", "Request failed: {error}")`.
- `ExecutionError` payload → maps `error.category` through `_ERROR_MESSAGES` (module-level dict)
  to produce a user-friendly message. The raw `error.detail` is **never** shown directly to the
  user.

`_ERROR_MESSAGES` format strings accept `{url}` and `{detail}` placeholders:

```python
_ERROR_MESSAGES = {
    ErrorCategory.NETWORK:  "Could not connect to {url}. Check that the server is running...",
    ErrorCategory.TIMEOUT:  "Request to {url} timed out. Try increasing the timeout...",
    ErrorCategory.TEMPLATE: "Template rendering failed: {detail}. Check variable names...",
    ErrorCategory.SCRIPT:   "Post-script execution failed: {detail}. Review the script...",
    ErrorCategory.HISTORY:  "History could not be recorded: {detail}.",
    ErrorCategory.UNKNOWN:  "An unexpected error occurred: {detail}.",
}
```

---

## Metrics

Two new Prometheus counters are registered in `MetricsManager._init_metrics()`:

| Counter | Labels | Tracking method |
|---------|--------|-----------------|
| `request_errors_total` | `category` | `track_request_error(category)` |
| `history_record_errors_total` | — | `track_history_record_error()` |

`category` label values match `ErrorCategory` string values: `network`, `timeout`, `template`,
`script`, `unknown`.

---

## Logging

All error paths log at `ERROR` level with structured key=value fields:

| Location | Log key | Fields |
|----------|---------|--------|
| `http_client.py` | `Request timed out` | `method`, `url` |
| `http_client.py` | `Connection failed` | `method`, `url` |
| `http_client.py` | `Request failed` | `method`, `url`, exception |
| `mcp_client_service.py` | `mcp_operation_timeout` | `url`, `operation`, `timeout` |
| `mcp_client_service.py` | `mcp_operation_failed` | `url`, `operation`, `category`, `detail` |
| `request_service.py` | `template_render_failed` | `url`, `detail` |
| `request_service.py` | `request_execution_failed` | `method`, `url`, `category`, `detail` |
| `request_service.py` | `history_record_failed` | `error` |
| `worker.py` | `RequestWorker failed` | `category`, `detail` |
| `tabs_presenter.py` | `request_error` | `category`, `message`, `detail` |

MCP operation start and success events log at `DEBUG` (off by default).

---

## Adding a New Error Category

1. Add a value to `ErrorCategory` in `pypost/models/errors.py`.
2. Add a message template to `_ERROR_MESSAGES` in `tabs_presenter.py`.
3. Raise or construct `ExecutionError(category=ErrorCategory.NEW, ...)` at the relevant site.
4. The `request_errors_total{category="new"}` counter is created automatically by Prometheus
   on first increment — no `MetricsManager` change is required.
5. Add tests covering the new category in the relevant test file.

---

## Backward Compatibility

| Contract | Change | Compatible? |
|----------|--------|-------------|
| `RequestService.execute()` signature | None | ✓ |
| `ExecutionResult` existing fields | `execution_error` added (default `None`) | ✓ |
| `HTTPClient.send_request()` signature | None | ✓ |
| `RequestWorker` instantiation | None | ✓ |
| `worker.error` signal | `Signal(str)` → `Signal(object)` | ✓ (handler accepts both) |
| `responses_received_total` metric | None | ✓ |
| `MCPClientService.run()` return | `ResponseData` on success; raises `ExecutionError` on error | ✓ (callers use `RequestService`) |
