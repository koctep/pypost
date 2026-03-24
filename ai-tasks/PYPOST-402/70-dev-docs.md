# Developer Documentation: PYPOST-402 — Retry and Alerting for Email Failures

**Date:** 2026-03-24

---

## Overview

PYPOST-402 adds two operational capabilities to PyPost's HTTP worker:

1. **Automatic retry with exponential backoff** — failed HTTP requests can be retried a
   configurable number of times before surfacing an error to the user.
2. **Structured alerting on exhaustion** — when all retries are used up, a JSON entry is
   written to a rotating log file and optionally forwarded to an HTTP webhook.

---

## New Files

### `pypost/models/retry.py`

Pydantic model that describes a per-request retry strategy.

```
RetryPolicy
├── max_retries: int          — number of retries (0 = no retry, default)
├── retry_delay_seconds: float — initial backoff delay in seconds (default 1.0)
├── retry_backoff_multiplier: float — exponential multiplier applied per attempt (default 2.0)
└── retryable_status_codes: List[int] — HTTP codes that trigger a retry (default 429/500/502/503/504)
```

Attach a `RetryPolicy` to any `RequestData.retry_policy` field. If the field is `None`
(the default), the request behaves exactly as before this feature.

### `pypost/core/alert_manager.py`

Handles alerting when a request exhausts all retries.

```
AlertPayload (dataclass)
└── to_dict() -> dict   — JSON-serialisable representation

AlertManager
├── __init__(log_path, webhook_url, webhook_auth_header)
│   log_path           — Path to rotating alert log; defaults to platform data dir
│   webhook_url        — Optional HTTP endpoint to POST alerts to
│   webhook_auth_header — Optional Authorization header value for the webhook
├── emit(payload: AlertPayload) -> None
│   Writes a JSON line to the log file and optionally POSTs to the webhook.
│   Webhook failures are caught and logged; they never propagate.
└── _send_webhook(payload)  — internal; sends via requests.post with 5 s timeout
```

**Alert log location (default):** `<user_data_dir>/pypost/pypost-alerts.log`
Rotates at 5 MB, keeps 3 backups.

---

## Modified Files

### `pypost/models/models.py` — `RequestData`

New optional field:

```python
retry_policy: Optional[RetryPolicy] = None
```

Serialises/deserialises automatically via Pydantic. Setting `max_retries=0` (default) is
equivalent to `retry_policy=None` in terms of behaviour.

### `pypost/models/settings.py` — `AppSettings`

Three new fields for application-level defaults:

```python
default_retry_policy: Optional[RetryPolicy] = None
alert_webhook_url: Optional[str] = None
alert_webhook_auth_header: Optional[str] = None
```

> **Note (TD-2):** `default_retry_policy` is persisted correctly but is not yet applied
> at runtime. See `60-review.md` TD-2.

### `pypost/core/metrics.py` — `MetricsManager`

Two new Prometheus counters:

| Metric | Labels | When incremented |
|--------|--------|------------------|
| `request_retries_total` | `method`, `status_category` | Every retry attempt |
| `email_notification_failures_total` | `endpoint` | When all retries are exhausted |

Tracking methods:

```python
metrics.track_retry_attempt(method: str, status_category: str) -> None
metrics.track_email_notification_failure(endpoint: str) -> None
```

### `pypost/core/request_service.py` — `RequestService`

**Constructor change:** accepts `alert_manager: AlertManager | None = None`.

**New private methods:**

`_execute_http_with_retry(request, variables, stream_callback, stop_flag, headers_callback, retry_callback, request_name) -> ResponseData`

Wraps `http_client.send_request` in a retry loop:

1. Attempt the request (attempt index starts at 0).
2. On a retryable HTTP status code or `ExecutionError`, call `retry_callback`, increment
   `request_retries_total`, then sleep with exponential backoff (capped at 60 s/attempt).
3. The backoff sleep is interruptible: `stop_flag` is polled every 100 ms.
4. When `attempt == max_retries` and the request still fails, call `_emit_exhaustion_alert`
   then re-raise the `ExecutionError` with `detail = "retries_attempted: N"`.

`_emit_exhaustion_alert(request, request_name, retries_attempted, error) -> None`

Increments `email_notification_failures_total` and, if an `AlertManager` is injected, calls
`alert_manager.emit()`.

**`execute()` change:** `retry_callback` parameter added (defaults to `None`); HTTP execution
is delegated to `_execute_http_with_retry` for all non-MCP requests.

### `pypost/core/worker.py` — `RequestWorker`

New signal:

```python
retry_attempt = Signal(int, int, object)  # attempt, max_retries, ExecutionError
```

The `run()` method defines an `on_retry` callback that emits this signal and passes it to
`service.execute(retry_callback=on_retry)`.

> **Note (TD-1):** `RequestWorker` does not yet inject `AlertManager` into `RequestService`.
> See `60-review.md` TD-1.

### `pypost/ui/presenters/tabs_presenter.py` — `TabsPresenter`

`_handle_send_request` connects `worker.retry_attempt`:

```python
worker.retry_attempt.connect(
    lambda attempt, max_r, _err, tab=sender_tab: self._on_retry_attempt(tab, attempt, max_r)
)
```

New handler:

```python
def _on_retry_attempt(self, tab: RequestTab, attempt: int, max_retries: int) -> None:
    tab.request_editor.send_btn.setText(f"Retrying… ({attempt} of {max_retries})")
```

The existing `_reset_tab_ui_state()` resets the button text on completion or error.

### `pypost/ui/dialogs/settings_dialog.py` — `SettingsDialog`

Six new form fields added under the existing settings:

| Field | Widget | Range |
|-------|--------|-------|
| Max Retries | `QSpinBox` | 0–10 |
| Retry Delay | `QDoubleSpinBox` | 0.1–30.0 s |
| Retry Backoff Multiplier | `QDoubleSpinBox` | 1.0–5.0 |
| Retryable Status Codes | `QLineEdit` | comma-separated integers |
| Alert Webhook URL | `QLineEdit` | optional URL |
| Alert Webhook Auth Header | `QLineEdit` | optional Bearer token |

On `accept()`, a `RetryPolicy` is constructed from the spin-box values and stored as
`AppSettings.default_retry_policy`.

---

## Data Flow

```
SettingsDialog  →  AppSettings.default_retry_policy  →  (TD-2: not yet applied)
                →  AppSettings.alert_webhook_url      →  (TD-1: not yet wired to AlertManager)

RequestData.retry_policy  ─────────────────────────────────────────────────────┐
                                                                                ↓
TabsPresenter._handle_send_request → RequestWorker.run()
    → RequestService.execute()
        → _execute_http_with_retry()
            retry loop: http_client.send_request()
            ├── on retryable failure: metrics.track_retry_attempt()
            │                         retry_callback() → worker.retry_attempt signal
            │                         → TabsPresenter._on_retry_attempt() (button text)
            └── on exhaustion: _emit_exhaustion_alert()
                               → metrics.track_email_notification_failure()
                               → AlertManager.emit()
                                   ├── RotatingFileHandler (pypost-alerts.log)
                                   └── requests.post(webhook_url)  [optional]
```

---

## Testing

| File | Coverage |
|------|----------|
| `tests/test_retry.py` | Retry logic: no-retry default, status-code retry, exception retry, callback, stop-flag, metrics, alert exhaustion, model validation |
| `tests/test_alert_manager.py` | Log file writing, multiple entries, nested path creation, webhook with/without auth, webhook failure resilience, JSON body |
| `tests/test_worker.py` | `TestRequestWorkerRetrySignal` — confirms `retry_attempt` signal is emitted when `retry_callback` is invoked |

Run tests:

```bash
python -m pytest tests/test_retry.py tests/test_alert_manager.py tests/test_worker.py -v
```

---

## Configuration Reference

### Per-request retry policy (programmatic / JSON)

```json
{
  "retry_policy": {
    "max_retries": 3,
    "retry_delay_seconds": 1.0,
    "retry_backoff_multiplier": 2.0,
    "retryable_status_codes": [429, 500, 502, 503, 504]
  }
}
```

Set `max_retries: 0` (or omit `retry_policy`) to disable retry for a specific request.

### Application-level defaults (Settings dialog)

Open **Settings** → configure *Max Retries*, *Retry Delay*, *Retry Backoff Multiplier*, and
*Retryable Status Codes*. These become the `AppSettings.default_retry_policy` and persist
across sessions.

### Alert webhook (Settings dialog)

Fill in *Alert Webhook URL* (e.g., `https://hooks.slack.com/…`) and optionally
*Alert Webhook Auth Header* (e.g., `Bearer <token>`). Webhook failures are swallowed and
logged at WARNING level; they never block the request flow.

---

## Observability

### Prometheus metrics

Query examples (Prometheus / Grafana):

```promql
# Retry rate by HTTP method
rate(request_retries_total[5m])

# Requests exhausting all retries by endpoint
rate(email_notification_failures_total[5m])
```

### Application log (structured key=value)

| Logger | Level | Event key | Meaning |
|--------|-------|-----------|---------|
| `pypost.core.request_service` | DEBUG | `http_attempt` | Start of each attempt |
| `pypost.core.request_service` | WARNING | `retryable_status` | Retryable HTTP status; will retry |
| `pypost.core.request_service` | WARNING | `retryable_error` | `ExecutionError` caught; will retry |
| `pypost.core.request_service` | DEBUG | `retry_backoff` | Entering backoff sleep |
| `pypost.core.request_service` | DEBUG | `retry_cancelled_during_backoff` | Stop flag raised mid-sleep |
| `pypost.core.request_service` | WARNING | `retry_exhausted` | All retries used; alert emitted |
| `pypost.core.alert_manager` | WARNING | `alert_emitted` | Alert written to log file |
| `pypost.core.alert_manager` | WARNING | `alert_webhook_failed` | Webhook delivery failed |

### Alert log file

Location: `<user_data_dir>/pypost/pypost-alerts.log` (platform-specific; e.g.,
`~/.local/share/pypost/pypost-alerts.log` on Linux).

Each line is a JSON object:

```json
{
  "timestamp": "2026-03-24T12:00:00.123456+00:00",
  "request_name": "Notify Users",
  "endpoint": "https://api.example.com/notify",
  "retries_attempted": 3,
  "final_error_category": "network",
  "final_error_message": "Connection refused"
}
```

---

## Known Gaps (see `60-review.md`)

| ID | Description |
|----|-------------|
| TD-1 | `AlertManager` not injected into `RequestWorker` — alerts never fire in production |
| TD-2 | `default_retry_policy` from `AppSettings` not applied at runtime |
| TD-3 | `AlertManager` logger/handler leak on repeated instantiation |
| TD-4 | Bare `assert` in retry exhaustion path; breaks under `-O` |
| TD-7 | `request_timeout` spin box missing from settings form layout |
