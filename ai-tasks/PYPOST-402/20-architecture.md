# Architecture: PYPOST-402 — Add Retry and Alerting for Email Failures

## Overview

This document describes the technical design for implementing retry strategy and operational
alerting for failed outbound HTTP requests in PyPost. The implementation follows existing
patterns: Pydantic models, DI-friendly services, QThread signal callbacks, and Prometheus
via `MetricsManager`.

---

## Design Principles

- **Backward compatibility**: `max_retries = 0` (default) preserves existing behaviour exactly.
- **Service-layer retry**: Retry logic lives in `RequestService`, not in the worker or HTTP
  client, to remain mockable and testable without Qt.
- **Callback injection**: The worker passes a `retry_callback` into `RequestService.execute()`
  to decouple signal emission from business logic.
- **Minimal surface area**: Only the files that genuinely need to change are touched.

---

## New Files

### 1. `pypost/models/retry.py` — `RetryPolicy`

A standalone Pydantic model so `RequestData` remains focused.

```python
from __future__ import annotations
from typing import List
from pydantic import BaseModel, Field


class RetryPolicy(BaseModel):
    max_retries: int = 0
    retry_delay_seconds: float = 1.0
    retry_backoff_multiplier: float = 2.0
    retryable_status_codes: List[int] = Field(
        default_factory=lambda: [429, 500, 502, 503, 504]
    )
```

**Notes:**
- `max_retries = 0` is the sentinel for "no retry" — no special flag needed.
- Pydantic field serialises/deserialises to JSON automatically; persistence is free.

---

### 2. `pypost/core/alert_manager.py` — `AlertManager`

Responsible for emitting structured alerts on retry exhaustion.

```python
from __future__ import annotations
import json
import logging
import logging.handlers
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from platformdirs import user_data_dir


@dataclass
class AlertPayload:
    request_name: str
    endpoint: str
    retries_attempted: int
    final_error_category: str
    final_error_message: str
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "request_name": self.request_name,
            "endpoint": self.endpoint,
            "retries_attempted": self.retries_attempted,
            "final_error_category": self.final_error_category,
            "final_error_message": self.final_error_message,
        }


class AlertManager:
    """Emits structured alerts to a rotating log file and/or HTTP webhook."""

    _LOG_FILENAME = "pypost-alerts.log"
    _MAX_BYTES = 5 * 1024 * 1024   # 5 MB per file
    _BACKUP_COUNT = 3

    def __init__(
        self,
        log_path: Optional[Path] = None,
        webhook_url: Optional[str] = None,
        webhook_auth_header: Optional[str] = None,
    ) -> None:
        resolved = log_path or Path(user_data_dir("pypost")) / self._LOG_FILENAME
        resolved.parent.mkdir(parents=True, exist_ok=True)

        self._webhook_url = webhook_url
        self._webhook_auth_header = webhook_auth_header

        handler = logging.handlers.RotatingFileHandler(
            resolved,
            maxBytes=self._MAX_BYTES,
            backupCount=self._BACKUP_COUNT,
            encoding="utf-8",
        )
        self._logger = logging.getLogger(f"pypost.alerts.{id(self)}")
        self._logger.propagate = False
        self._logger.setLevel(logging.INFO)
        self._logger.addHandler(handler)

    def emit(self, payload: AlertPayload) -> None:
        """Write JSON alert to the rotating log file and optionally send to webhook."""
        self._logger.info(json.dumps(payload.to_dict()))
        if self._webhook_url:
            self._send_webhook(payload)

    def _send_webhook(self, payload: AlertPayload) -> None:
        headers = {"Content-Type": "application/json"}
        if self._webhook_auth_header:
            headers["Authorization"] = self._webhook_auth_header
        try:
            httpx.post(
                self._webhook_url,
                json=payload.to_dict(),
                headers=headers,
                timeout=5.0,
            )
        except Exception:  # noqa: BLE001
            pass  # Webhook failure must never crash the application
```

**Design decisions:**
- `RotatingFileHandler` ensures the log never grows unbounded.
- `httpx` (already a dependency) is used for the webhook; failures are swallowed so an
  unreachable webhook never propagates to the user.
- Constructor receives optional `log_path` and `webhook_url` for DI / testability.
- Logger instance is private (`propagate=False`) to avoid polluting the root logger.

---

## Modified Files

### 3. `pypost/models/models.py` — `RequestData`

Add an optional `retry_policy` field. Default `None` means "no retry" (backward compat).

```python
# new import at top
from pypost.models.retry import RetryPolicy

class RequestData(BaseModel):
    # ... existing fields unchanged ...
    retry_policy: Optional[RetryPolicy] = None
```

---

### 4. `pypost/models/settings.py` — `AppSettings`

Add optional alert webhook configuration (stretch goal from FR-4).

```python
class AppSettings(BaseModel):
    # ... existing fields unchanged ...
    alert_webhook_url: Optional[str] = None
    alert_webhook_auth_header: Optional[str] = None
```

---

### 5. `pypost/core/metrics.py` — `MetricsManager`

Add two new Prometheus counters and corresponding tracking methods.

**New counters (added alongside existing ones):**

```python
self._request_retries_total = Counter(
    "request_retries_total",
    "Number of retry attempts made",
    ["method", "status_category"],
    registry=self._registry,
)
self._email_notification_failures_total = Counter(
    "email_notification_failures_total",
    "Number of requests that exhausted all retries",
    ["endpoint"],
    registry=self._registry,
)
```

**New tracking methods:**

```python
def track_retry_attempt(self, method: str, status_category: str) -> None:
    self._request_retries_total.labels(
        method=method.upper(), status_category=status_category
    ).inc()

def track_email_notification_failure(self, endpoint: str) -> None:
    self._email_notification_failures_total.labels(endpoint=endpoint).inc()
```

---

### 6. `pypost/core/request_service.py` — `RequestService`

**Signature additions:**

```python
from typing import Callable, Optional
from pypost.core.alert_manager import AlertManager, AlertPayload
from pypost.models.retry import RetryPolicy


class RequestService:
    def __init__(
        self,
        http_client: ...,
        metrics: MetricsManager,
        history_manager: ...,
        template_service: ...,
        alert_manager: Optional[AlertManager] = None,  # NEW
    ) -> None:
        ...
        self._alert_manager = alert_manager
```

**`execute()` signature additions:**

```python
def execute(
    self,
    request: RequestData,
    variables: Dict[str, Any] = None,
    stream_callback: Callable[[str], None] = None,
    stop_flag: Callable[[], bool] = None,
    headers_callback: Callable[[int, Dict], None] = None,
    collection_name: str | None = None,
    request_name: str | None = None,
    retry_callback: Callable[[int, int, ExecutionError], None] | None = None,  # NEW
) -> ExecutionResult:
```

**Retry loop — new private method `_execute_http_with_retry()`:**

```python
def _execute_http_with_retry(
    self,
    request: RequestData,
    variables: Dict[str, Any],
    stream_callback: Callable[[str], None] | None,
    stop_flag: Callable[[], bool] | None,
    headers_callback: Callable[[int, Dict], None] | None,
    retry_callback: Callable[[int, int, ExecutionError], None] | None,
    request_name: str,
) -> ResponseData:
    """Execute HTTP request with optional retry and exponential back-off."""
    import time

    policy: RetryPolicy | None = request.retry_policy
    max_retries = policy.max_retries if policy else 0
    delay = policy.retry_delay_seconds if policy else 1.0
    multiplier = policy.retry_backoff_multiplier if policy else 2.0
    retryable_codes = set(policy.retryable_status_codes) if policy else set()

    last_error: ExecutionError | None = None

    for attempt in range(max_retries + 1):  # attempt 0 = first try
        if stop_flag and stop_flag():
            raise ExecutionError(
                category=ErrorCategory.NETWORK,
                message="Request cancelled",
                detail="Cancelled during retry delay",
            )

        try:
            response = self._http_client.send_request(
                request, variables, stream_callback, stop_flag, headers_callback
            )
            if response.status_code not in retryable_codes or attempt == max_retries:
                return response
            # Retryable status code and retries remain
            last_error = ExecutionError(
                category=ErrorCategory.NETWORK,
                message=f"HTTP {response.status_code}",
                detail=f"retries_attempted: {attempt}",
            )
        except ExecutionError as exc:
            last_error = exc
            if attempt == max_retries:
                last_error.detail = f"retries_attempted: {attempt}"
                raise last_error

        # Emit retry signal and track metrics
        self._metrics.track_retry_attempt(request.method, last_error.category.value)
        if retry_callback:
            retry_callback(attempt + 1, max_retries, last_error)

        # Exponential back-off (capped at 60 s)
        wait = min(delay * (multiplier ** attempt), 60.0)
        end = time.monotonic() + wait
        while time.monotonic() < end:
            if stop_flag and stop_flag():
                raise ExecutionError(
                    category=ErrorCategory.NETWORK,
                    message="Request cancelled",
                    detail="Cancelled during retry delay",
                )
            time.sleep(0.1)

        delay = delay  # next iteration uses multiplier via exponent

    # Exhaustion — emit alert
    assert last_error is not None
    last_error.detail = f"retries_attempted: {max_retries}"
    self._emit_exhaustion_alert(request, request_name, max_retries, last_error)
    raise last_error


def _emit_exhaustion_alert(
    self,
    request: RequestData,
    request_name: str,
    retries_attempted: int,
    error: ExecutionError,
) -> None:
    self._metrics.track_email_notification_failure(request.url)
    if self._alert_manager:
        self._alert_manager.emit(AlertPayload(
            request_name=request_name or request.name,
            endpoint=request.url,
            retries_attempted=retries_attempted,
            final_error_category=error.category.value,
            final_error_message=error.message,
        ))
```

**`execute()` change:** replace the direct `self._http_client.send_request(...)` call with
`self._execute_http_with_retry(...)`.

---

### 7. `pypost/core/worker.py` — `RequestWorker`

Add the `retry_attempt` signal and wire the callback.

```python
class RequestWorker(QThread):
    finished = Signal(ResponseData)
    error = Signal(object)
    retry_attempt = Signal(int, int, object)  # NEW: attempt, max, ExecutionError
    env_update = Signal(dict)
    script_output = Signal(list, str)
    chunk_received = Signal(str)
    headers_received = Signal(int, dict)

    def run(self) -> None:
        def _retry_cb(attempt: int, max_retries: int, err: ExecutionError) -> None:
            self.retry_attempt.emit(attempt, max_retries, err)

        result = self._service.execute(
            ...,
            retry_callback=_retry_cb,  # NEW
        )
        ...
```

---

### 8. `pypost/ui/presenters/tabs_presenter.py` — `TabsPresenter`

Connect the new signal and display retry progress.

**In `_handle_send_request`:**

```python
worker.retry_attempt.connect(
    lambda attempt, max_r, _err, tab=sender_tab: self._on_retry_attempt(
        tab, attempt, max_r
    )
)
```

**New handler:**

```python
def _on_retry_attempt(self, tab: RequestTab, attempt: int, max_retries: int) -> None:
    tab.request_editor.send_btn.setText(
        f"Retrying\u2026 ({attempt} of {max_retries})"
    )
```

**`_reset_tab_ui_state()`** already resets the button text on completion/error — no change
needed there.

---

### 9. Settings Dialog — Retry Policy Fields (FR-6 / AC-9)

The settings dialog (identified at `pypost/ui/dialogs/settings_dialog.py`) must expose:

- `max_retries` (SpinBox, 0–10)
- `retry_delay_seconds` (DoubleSpinBox, 0.1–30.0)
- `retry_backoff_multiplier` (DoubleSpinBox, 1.0–5.0)
- `retryable_status_codes` (line-edit with comma-separated integers)
- `alert_webhook_url` (line-edit, optional)
- `alert_webhook_auth_header` (line-edit, optional)

These settings apply as **application-level defaults** — they populate the `RetryPolicy`
when a request does not have its own policy. Existing per-request overrides take precedence.

**Implementation note:** `AppSettings` carries the defaults; `RequestData.retry_policy`
(if non-`None`) overrides them. The `RequestService` resolves effective policy at execution
time.

---

## Sequence Diagram — Retry Flow

```
TabsPresenter          RequestWorker       RequestService           MetricsManager   AlertManager
     |                      |                    |                        |               |
     |  worker.run()        |                    |                        |               |
     |--------------------> |                    |                        |               |
     |                      | service.execute()  |                        |               |
     |                      |------------------> |                        |               |
     |                      |                    | http_client.send()     |               |
     |                      |                    |-----> [503 response]   |               |
     |                      |                    |                        |               |
     |                      |                    | track_retry_attempt()  |               |
     |                      |                    |----------------------->|               |
     |                      | retry_attempt(1,3) |                        |               |
     |                      |<------------------ |                        |               |
     | _on_retry_attempt()  |                    |                        |               |
     |<--------------------- |                    |                        |               |
     |  btn "Retrying…(1/3)"|                    |                        |               |
     |                      |                    | [wait backoff]         |               |
     |                      |                    | [stop_flag poll]       |               |
     |                      |                    | http_client.send() x3  |               |
     |                      |                    |-----> [exhausted]      |               |
     |                      |                    |                        |               |
     |                      |                    | track_email_failure()  |               |
     |                      |                    |----------------------->|               |
     |                      |                    | alert_manager.emit()   |               |
     |                      |                    |---------------------------------->     |
     |                      |                    |                        |  [log JSON]   |
     |                      |                    | raise ExecutionError   |               |
     |                      | error.emit()       |                        |               |
     |                      |<------------------ |                        |               |
     | _on_request_error()  |                    |                        |               |
     |<--------------------- |                    |                        |               |
```

---

## File Change Summary

| File | Change Type | Scope |
|------|-------------|-------|
| `pypost/models/retry.py` | **New** | `RetryPolicy` Pydantic model |
| `pypost/core/alert_manager.py` | **New** | `AlertPayload` + `AlertManager` |
| `pypost/models/models.py` | Modify | Add `retry_policy` to `RequestData` |
| `pypost/models/settings.py` | Modify | Add `alert_webhook_url`, `alert_webhook_auth_header` |
| `pypost/core/metrics.py` | Modify | 2 new counters + 2 tracking methods |
| `pypost/core/request_service.py` | Modify | `_execute_http_with_retry`, `_emit_exhaustion_alert`, DI for `AlertManager` |
| `pypost/core/worker.py` | Modify | `retry_attempt` signal, `retry_callback` wiring |
| `pypost/ui/presenters/tabs_presenter.py` | Modify | Connect `retry_attempt`, `_on_retry_attempt` handler |
| `pypost/ui/dialogs/settings_dialog.py` | Modify | Retry policy + alert webhook UI fields |
| `tests/test_retry.py` | **New** | Unit tests for retry logic (≥ 90 % branch coverage) |
| `tests/test_alert_manager.py` | **New** | Unit tests for `AlertManager` |
| `tests/test_worker.py` | Modify | Test `retry_attempt` signal emission |

---

## Dependency Notes

- `httpx` is used for the optional webhook in `AlertManager`. Confirm it is already in
  `requirements.txt`; if not, add it (or reuse `requests` which is already present).
- No new Qt / PySide6 dependencies are introduced.
- `platformdirs` is already a dependency (used by `HistoryManager`).

---

## Acceptance Criteria Mapping

| AC | Implementation point |
|----|----------------------|
| AC-1 | `_execute_http_with_retry` retries up to `max_retries` on `retryable_status_codes` |
| AC-2 | `retry_callback` → `worker.retry_attempt.emit()` per attempt |
| AC-3 | `stop_flag` polled inside back-off sleep loop (100 ms granularity) |
| AC-4 | `metrics.track_retry_attempt()` called per attempt |
| AC-5 | `metrics.track_email_notification_failure()` called on exhaustion |
| AC-6 | `alert_manager.emit()` writes JSON to `pypost-alerts.log` on exhaustion |
| AC-7 | Default `retry_policy=None` → `max_retries=0` → no retry path taken |
| AC-8 | `tests/test_retry.py` + `tests/test_alert_manager.py` at ≥ 90 % branch coverage |
| AC-9 | Settings dialog exposes all `RetryPolicy` fields and saves to `AppSettings` |
