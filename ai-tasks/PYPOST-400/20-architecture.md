# PYPOST-400: Architecture — Stabilize Post Publishing API Error Handling

## 1. Overview

This document describes the design for structured error handling across the post publishing flow.
The solution introduces a shared error model, threads it through each execution layer, and surfaces
actionable, category-specific messages in the UI while adding Prometheus metrics coverage.

---

## 2. Affected Files

| File | Change Type |
|------|-------------|
| `pypost/models/errors.py` | **New** — shared `ErrorCategory` + `ExecutionError` |
| `pypost/core/http_client.py` | Modify — catch exceptions, raise `ExecutionError` |
| `pypost/core/mcp_client_service.py` | Modify — raise `ExecutionError` instead of fake status codes |
| `pypost/core/request_service.py` | Modify — catch errors, populate `ExecutionResult` |
| `pypost/models/request_service.py` | — (`ExecutionResult` lives in `request_service.py`, add field) |
| `pypost/core/worker.py` | Modify — signal carries `ExecutionError`, not raw string |
| `pypost/core/metrics.py` | Modify — add error + history-failure counters |
| `pypost/ui/presenters/tabs_presenter.py` | Modify — map `ErrorCategory` to actionable message |

---

## 3. New Module: `pypost/models/errors.py`

### 3.1 `ErrorCategory` enum

```python
import enum

class ErrorCategory(str, enum.Enum):
    NETWORK  = "network"
    TIMEOUT  = "timeout"
    TEMPLATE = "template"
    SCRIPT   = "script"
    HISTORY  = "history"
    UNKNOWN  = "unknown"
```

Using `str` as the mixin allows the value to be used directly as a Prometheus label without an
extra `.value` call.

### 3.2 `ExecutionError` exception

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ExecutionError(Exception):
    category: ErrorCategory
    message: str                        # Human-readable, actionable
    detail: Optional[str] = field(default=None)  # Raw exception string; logs/debug only

    def __str__(self) -> str:
        return self.message
```

Making `ExecutionError` an `Exception` subclass lets it be **raised** (by `HTTPClient`,
`MCPClientService`) and also **stored** in `ExecutionResult`. The `detail` field holds the raw
exception string and is never shown directly in the UI.

---

## 4. `HTTPClient` Changes (`pypost/core/http_client.py`)

### 4.1 Import

```python
from pypost.models.errors import ErrorCategory, ExecutionError
```

### 4.2 `send_request()` — wrap the `except Exception` block

**Current (lines ~180–188):**
```python
except Exception as e:
    logger.error("Request failed: ...")
    raise
```

**Replace with:**
```python
except requests.Timeout as exc:
    raise ExecutionError(
        category=ErrorCategory.TIMEOUT,
        message=f"Request to {url} timed out.",
        detail=str(exc),
    ) from exc
except requests.ConnectionError as exc:
    raise ExecutionError(
        category=ErrorCategory.NETWORK,
        message=f"Could not connect to {url}.",
        detail=str(exc),
    ) from exc
except requests.RequestException as exc:
    raise ExecutionError(
        category=ErrorCategory.UNKNOWN,
        message="An unexpected request error occurred.",
        detail=str(exc),
    ) from exc
```

Note: `requests.Timeout` is a subclass of `requests.ConnectionError` in some versions; always
catch it first. The template-rendering step (`_prepare_request_kwargs`) may raise `jinja2`
exceptions — those are handled in `RequestService`, not here, because template rendering is also
called before `send_request`.

---

## 5. `MCPClientService` Changes (`pypost/core/mcp_client_service.py`)

**REQ-5.1** — Remove fake HTTP status codes (500, 504) from internal error returns. Raise
`ExecutionError` instead; `RequestService._execute_mcp()` catches it and returns a
`ResponseData` placeholder so the UI still shows the error body.

### 5.1 Import

```python
from pypost.models.errors import ErrorCategory, ExecutionError
```

### 5.2 `run()` — replace error `ResponseData` returns with raises

**Timeout branch:**
```python
except asyncio.TimeoutError as exc:
    raise ExecutionError(
        category=ErrorCategory.TIMEOUT,
        message=f"MCP request timed out after {MCP_TOTAL_TIMEOUT}s.",
        detail=str(exc),
    ) from exc
```

**General exception branch:**
```python
except Exception as exc:
    err_msg = str(exc)
    if isinstance(exc, BaseExceptionGroup):
        err_msg = "; ".join(str(x) for x in exc.exceptions)
    err_type = type(exc).__name__
    if "ConnectError" in err_type or "connection" in err_msg.lower():
        category = ErrorCategory.NETWORK
        message = "Could not connect to MCP server. Is it running?"
    elif "Timeout" in err_type or "timeout" in err_msg.lower():
        category = ErrorCategory.TIMEOUT
        message = "MCP server did not respond in time."
    else:
        category = ErrorCategory.UNKNOWN
        message = "MCP operation failed."
    raise ExecutionError(category=category, message=message, detail=err_msg) from exc
```

The success branch (status_code=200 ResponseData) is unchanged.

---

## 6. `RequestService` Changes (`pypost/core/request_service.py`)

### 6.1 `ExecutionResult` — add `execution_error` field (additive, backward-compatible)

```python
@dataclass
class ExecutionResult:
    response: ResponseData
    updated_variables: Dict[str, Any]
    script_logs: List[str]
    script_error: Optional[str]
    execution_error: Optional["ExecutionError"] = None  # New field
```

Default `None` keeps all existing callers working unchanged (REQ-7.3).

### 6.2 Import

```python
from pypost.models.errors import ErrorCategory, ExecutionError
```

### 6.3 `execute()` — template rendering guard (REQ-3.2)

Wrap the URL/body template rendering that happens before HTTP dispatch:

```python
try:
    if request.method == "MCP":
        response = self._execute_mcp(request, variables, headers_callback)
    else:
        response = self.http_client.send_request(...)
except ExecutionError as exc:
    if self._metrics:
        self._metrics.track_request_error(exc.category)
    return ExecutionResult(
        response=_error_response(exc),
        updated_variables={},
        script_logs=[],
        script_error=None,
        execution_error=exc,
    )
```

Template rendering errors (Jinja2 `TemplateError`) are caught around the pre-flight template call
and re-raised as `ExecutionError(category=ErrorCategory.TEMPLATE, ...)` before HTTP dispatch:

```python
try:
    resolved_url = self._template_service.render_string(request.url, variables)
except Exception as exc:
    raise ExecutionError(
        category=ErrorCategory.TEMPLATE,
        message="Template rendering failed.",
        detail=str(exc),
    ) from exc
```

This guard is placed at the top of `execute()` before calling `http_client.send_request()`.

### 6.4 Script error — use `ExecutionError` (REQ-3.3)

`ScriptExecutor.execute()` already returns `(vars, logs, error_str)`. Wrap `script_error` when
populating `ExecutionResult`:

```python
exec_error_from_script = None
if script_error:
    exec_error_from_script = ExecutionError(
        category=ErrorCategory.SCRIPT,
        message="Post-script execution failed.",
        detail=script_error,
    )
    if self._metrics:
        self._metrics.track_request_error(ErrorCategory.SCRIPT)

result = ExecutionResult(
    response=response,
    updated_variables=updated_variables,
    script_logs=script_logs,
    script_error=script_error,          # Keep original str field (backward compat)
    execution_error=exec_error_from_script,
)
```

### 6.5 History recording failure — track via metrics (REQ-3.4)

**Current:**
```python
except Exception as exc:
    logger.error("history_record_failed error=%s", exc)
```

**Replace with:**
```python
except Exception as exc:
    logger.error("history_record_failed error=%s", exc)
    if self._metrics:
        self._metrics.track_history_record_error()
```

### 6.6 `_error_response()` helper (private, in same file)

```python
def _error_response(exc: "ExecutionError") -> ResponseData:
    """Synthesises a ResponseData placeholder for failed requests."""
    import json as _json
    body = _json.dumps({"error": exc.message, "detail": exc.detail})
    return ResponseData(
        status_code=0,
        headers={},
        body=body,
        elapsed_time=0.0,
        size=len(body.encode("utf-8")),
    )
```

`status_code=0` indicates a client-side failure (no response was received).

---

## 7. `RequestWorker` Changes (`pypost/core/worker.py`)

### 7.1 Signal type change (REQ-4.1)

```python
# Before
error = Signal(str)

# After
error = Signal(object)   # carries ExecutionError; falls back to str for cancellation
```

`Signal(object)` passes any Python object. The payload contract is:
- `ExecutionError` instance — for real failures
- `str` — only for the cancellation/stop path (no change needed there)

### 7.2 `run()` exception handling

```python
except ExecutionError as exc:
    logger.error("RequestWorker failed category=%s detail=%s", exc.category, exc.detail)
    self.error.emit(exc)
except Exception as exc:
    logger.error("RequestWorker unexpected error: %s", exc, exc_info=True)
    self.error.emit(ExecutionError(
        category=ErrorCategory.UNKNOWN,
        message="An unexpected error occurred.",
        detail=str(exc),
    ))
```

Import: `from pypost.models.errors import ErrorCategory, ExecutionError`

---

## 8. `tabs_presenter.py` Changes (`pypost/ui/presenters/tabs_presenter.py`)

### 8.1 Import

```python
from pypost.models.errors import ErrorCategory, ExecutionError
```

### 8.2 `_on_request_error()` — structured dispatch (REQ-4.2, REQ-4.3)

```python
_ERROR_MESSAGES = {
    ErrorCategory.NETWORK: (
        "Could not connect to {url}. Check that the server is running and reachable."
    ),
    ErrorCategory.TIMEOUT: (
        "Request to {url} timed out. Try increasing the timeout or check server load."
    ),
    ErrorCategory.TEMPLATE: (
        "Template rendering failed: {detail}. Check variable names and syntax."
    ),
    ErrorCategory.SCRIPT: (
        "Post-script execution failed: {detail}. Review the script for errors."
    ),
    ErrorCategory.HISTORY: (
        "History could not be recorded: {detail}."
    ),
    ErrorCategory.UNKNOWN: (
        "An unexpected error occurred: {detail}."
    ),
}

def _on_request_error(self, tab: RequestTab, error) -> None:
    self._reset_tab_ui_state(tab)

    # Cancellation path (still a plain string)
    if isinstance(error, str):
        if "cancelled" in error.lower() or "aborted" in error.lower():
            logger.info("request_cancelled error_msg=%s", error)
            return
        logger.error("request_error error_msg=%s", error)
        QMessageBox.critical(self._tabs, "Error", f"Request failed: {error}")
        return

    # Structured ExecutionError path
    if isinstance(error, ExecutionError):
        if error.detail and (
            "cancelled" in error.detail.lower() or "aborted" in error.detail.lower()
        ):
            logger.info("request_cancelled category=%s", error.category)
            return

        url = tab.request_data.url if tab.request_data else ""
        template = _ERROR_MESSAGES.get(error.category, _ERROR_MESSAGES[ErrorCategory.UNKNOWN])
        user_msg = template.format(url=url, detail=error.detail or error.message)

        logger.error(
            "request_error category=%s message=%s detail=%s",
            error.category, error.message, error.detail,
        )
        QMessageBox.critical(self._tabs, "Request Error", user_msg)
```

The `_ERROR_MESSAGES` dict is a module-level constant (not a class attribute) to keep the method
clean and allow easy testing of message templates.

---

## 9. `MetricsManager` Changes (`pypost/core/metrics.py`)

### 9.1 New counters in `_init_metrics()`

```python
self.request_errors = Counter(
    'request_errors_total',
    'Number of request execution errors by category',
    ['category'],
    registry=self.registry
)

self.history_record_errors = Counter(
    'history_record_errors_total',
    'Number of history recording failures',
    registry=self.registry
)
```

### 9.2 New tracking methods

```python
def track_request_error(self, category: "ErrorCategory") -> None:
    self.request_errors.labels(category=category).inc()

def track_history_record_error(self) -> None:
    self.history_record_errors.inc()
```

Import: `from pypost.models.errors import ErrorCategory`

---

## 10. Data Flow Diagram

```
User clicks Send
      │
      ▼
tabs_presenter._handle_send_request()
      │  creates RequestWorker
      ▼
RequestWorker.run()  ──────────────────────────────────────────────┐
      │                                                             │
      │  calls RequestService.execute()                            │ ExecutionError
      │                                                            │ → error.emit(ExecutionError)
      ▼                                                             │
RequestService.execute()                                           │
  ├─ template render guard ──── TemplateError → ExecutionError ───►│
  ├─ HTTPClient.send_request()                                      │
  │    ├─ requests.Timeout     → ExecutionError(TIMEOUT)  ────────►│
  │    ├─ requests.ConnError   → ExecutionError(NETWORK)  ────────►│
  │    └─ requests.RequestExc  → ExecutionError(UNKNOWN)  ────────►│
  ├─ MCPClientService.run()                                         │
  │    ├─ asyncio.TimeoutError → ExecutionError(TIMEOUT)  ────────►│
  │    └─ ConnectError / other → ExecutionError(NETWORK/UNKNOWN) ──►│
  ├─ ExecutionError caught → track_request_error(category)         │
  │                        → return ExecutionResult(execution_error)│
  ├─ ScriptExecutor.execute()                                       │
  │    └─ script_error str → ExecutionError(SCRIPT)               │
  └─ history record failure → track_history_record_error()         │
                                                                    │
      ▼  (happy path)                                               │
  finished.emit(ResponseData)                                       │
      │                                                             │
      ▼                                                             ▼
_on_request_finished()                               _on_request_error(tab, ExecutionError)
  display response                                     map category → user message
                                                       QMessageBox.critical(user_msg)
```

---

## 11. Backward Compatibility Guarantees (REQ-7)

| Contract | How Preserved |
|----------|---------------|
| `RequestService.execute()` signature | Unchanged |
| `ExecutionResult` existing fields | Unchanged; `execution_error` is additive with default `None` |
| `HTTPClient.send_request()` signature | Unchanged |
| `RequestWorker` instantiation | Unchanged |
| `worker.error` signal consumers | `_on_request_error` handles both `str` and `ExecutionError` |
| `responses_received_total` metric | Counter and `track_response_received()` unchanged |
| `MCPClientService.run()` return type | Still returns `ResponseData` on success; raises on failure (callers already handle this via `RequestService`) |

---

## 12. Test Strategy

Existing tests must pass without modification (REQ-7.1). New behaviour must be verified by new
tests. Key new test cases:

| Test | File | Assertion |
|------|------|-----------|
| `HTTPClient` raises `ExecutionError(TIMEOUT)` on `requests.Timeout` | `test_http_client.py` | `ExecutionError.category == TIMEOUT` |
| `HTTPClient` raises `ExecutionError(NETWORK)` on `ConnectionError` | `test_http_client.py` | `ExecutionError.category == NETWORK` |
| `RequestService.execute()` returns result (never raises) | `test_request_service.py` | `isinstance(result, ExecutionResult)` |
| Template error populates `execution_error.category == TEMPLATE` | `test_request_service.py` | field check |
| Script error populates `execution_error.category == SCRIPT` | `test_request_service.py` | field check |
| History failure increments `history_record_errors_total` | `test_request_service.py` | `mock_metrics.track_history_record_error.called` |
| `RequestWorker.error` emits `ExecutionError` object | `test_worker.py` | signal payload type |
| `_on_request_error` displays category message (no raw exception) | `test_tabs_presenter.py` | `QMessageBox` text check |
| `MCPClientService` raises `ExecutionError(TIMEOUT)` on timeout | `test_mcp_client_service.py` | exception type |

---

## 13. Implementation Order

1. `pypost/models/errors.py` — create `ErrorCategory` + `ExecutionError`
2. `pypost/core/metrics.py` — add two counters + tracking methods
3. `pypost/core/http_client.py` — replace bare `raise` with typed `ExecutionError`
4. `pypost/core/mcp_client_service.py` — replace fake-status returns with raises
5. `pypost/core/request_service.py` — catch errors, extend `ExecutionResult`, track history failure
6. `pypost/core/worker.py` — change signal type, emit structured error
7. `pypost/ui/presenters/tabs_presenter.py` — add `_ERROR_MESSAGES`, update handler
