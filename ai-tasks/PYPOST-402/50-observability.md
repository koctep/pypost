# Observability: PYPOST-402 — Add Retry and Alerting for Email Failures

## Scope

This document records observability additions made during the senior engineer review pass.
The implementation already contained Prometheus counters and a structured alert log (both
designed in `20-architecture.md`); this pass filled the gaps in standard Python logging
coverage.

---

## What Was Already in Place (from implementation)

### Prometheus Metrics (`pypost/core/metrics.py`)

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `request_retries_total` | Counter | `method`, `status_category` | Incremented on each retry attempt |
| `email_notification_failures_total` | Counter | `endpoint` | Incremented when all retries are exhausted |

Exposed on the existing `/metrics` Prometheus endpoint.

### Structured Alert Log (`pypost/core/alert_manager.py`)

`AlertManager` writes a JSON line to a rotating file (`pypost-alerts.log`, 5 MB × 3 backups)
on every retry exhaustion event. Optionally forwards the same payload to an HTTP webhook.
Fields: `timestamp`, `request_name`, `endpoint`, `retries_attempted`, `final_error_category`,
`final_error_message`.

---

## Gaps Found

1. **No logging inside the retry loop** — Per-attempt activity, backoff waits, and
   mid-backoff cancellations were invisible to the application log.
2. **`_emit_exhaustion_alert` had no standard-logger entry** — Exhaustion was silently
   counted by the metric and forwarded to the alert file, but nothing appeared in the
   main application log.
3. **`alert_manager.py` had no module-level logger** — Webhook failures were swallowed
   with a bare `pass`; `emit()` did not surface in the application log at all.

---

## Changes Made

### `pypost/core/request_service.py`

**`_execute_http_with_retry`** — three new structured log calls:

| Log level | Event key | When emitted |
|-----------|-----------|--------------|
| `DEBUG` | `http_attempt` | Start of each attempt (attempt index, max_retries) |
| `WARNING` | `retryable_status` | Retryable HTTP status received; will retry |
| `WARNING` | `retryable_error` | `ExecutionError` caught; will retry |
| `DEBUG` | `retry_backoff` | Before entering the backoff sleep (wait_seconds logged) |
| `DEBUG` | `retry_cancelled_during_backoff` | `stop_flag` raised mid-backoff |

**`_emit_exhaustion_alert`** — one new structured log call:

| Log level | Event key | When emitted |
|-----------|-----------|--------------|
| `WARNING` | `retry_exhausted` | Immediately before Prometheus counter + alert file write |

Fields logged: `method`, `url`, `request_name`, `retries`, `error_category`, `error`.

---

### `pypost/core/alert_manager.py`

- Added `logger = logging.getLogger(__name__)` at module level.

**`emit()`** — one new structured log call:

| Log level | Event key | When emitted |
|-----------|-----------|--------------|
| `WARNING` | `alert_emitted` | After the alert file write, before the optional webhook |

Fields: `request_name`, `endpoint`, `retries`, `error_category`, `webhook` (yes/no).

**`_send_webhook()`** — exception handler changed from `pass` to:

| Log level | Event key | When emitted |
|-----------|-----------|--------------|
| `WARNING` | `alert_webhook_failed` | On any exception from `requests.post()` |

Fields: `url`, `error`.

---

## Log Format

All new log statements use key=value pairs consistent with the existing logging style in the
codebase (e.g., `method=GET url='http://…' attempt=1 max_retries=3`). This makes them
grep-friendly and compatible with structured log parsers (e.g., Vector, Loki).

Example output at WARNING level for a full retry cycle:

```
WARNING pypost.core.request_service: retryable_status method=GET url='http://api/ep' status=503 attempt=0 max_retries=2
WARNING pypost.core.request_service: retryable_status method=GET url='http://api/ep' status=503 attempt=1 max_retries=2
WARNING pypost.core.request_service: retry_exhausted method=GET url='http://api/ep' request_name='My Request' retries=2 error_category=ErrorCategory.NETWORK error=HTTP 503
WARNING pypost.core.alert_manager: alert_emitted request_name='My Request' endpoint='http://api/ep' retries=2 error_category=network webhook=no
```

---

## Files Modified

| File | Change |
|------|--------|
| `pypost/core/request_service.py` | 5 new `logger.*` calls in `_execute_http_with_retry`; 1 in `_emit_exhaustion_alert` |
| `pypost/core/alert_manager.py` | Module-level `logger`; 1 `logger.warning` in `emit()`; 1 `logger.warning` replacing `pass` in `_send_webhook` |
