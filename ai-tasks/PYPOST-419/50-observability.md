# PYPOST-419 — Observability

## Summary

Three targeted debug-log additions were made to make the policy resolution path fully
observable at runtime. No metrics or alerting changes were required — the existing
`track_retry_attempt` / `track_email_notification_failure` calls already capture retry-path
activity; the gap was traceability of *which* policy tier was selected.

---

## Gaps Identified

| Gap | Location | Risk |
|-----|----------|------|
| Policy source (per-request / app-default / hardcoded-fallback) not logged | `_execute_http_with_retry` | Cannot diagnose mis-routed policy tier from logs alone |
| `default_retry_policy` injection not logged at `RequestService` construction | `RequestService.__init__` | Inconsistent with existing `template_service` / `alert_manager` pattern |
| `default_retry_policy` forwarding not logged at `RequestWorker` construction | `RequestWorker.__init__` | Inconsistent with existing `template_service` / `alert_manager` pattern |

---

## Changes Made

### 1 — `RequestService.__init__` — injection log

**File**: `pypost/core/request_service.py`

```python
logger.debug(
    "RequestService: default_retry_policy_injected=%s max_retries=%s",
    default_retry_policy is not None,
    default_retry_policy.max_retries if default_retry_policy is not None else "N/A",
)
```

Logged unconditionally (value may be `False / N/A`) so that the absence of an injected
policy is also visible. Mirrors the existing `template_service` conditional log.

---

### 2 — `_execute_http_with_retry` — policy resolution source log

**File**: `pypost/core/request_service.py`

```python
_policy_source = (
    "per_request" if request.retry_policy is not None
    else "app_default" if self._default_retry_policy is not None
    else "hardcoded_fallback"
)
logger.debug(
    "retry_policy_resolved method=%s url=%r source=%s max_retries=%d",
    request.method, request.url, _policy_source, policy.max_retries if policy else 0,
)
```

Emitted once per request, immediately after the two-line policy resolution added by
PYPOST-419. Tells the operator exactly which tier provided the effective policy — the
primary observability signal for this fix.

**Log examples**:

```
DEBUG retry_policy_resolved method=GET url='https://api.example.com/users' source=per_request max_retries=1
DEBUG retry_policy_resolved method=POST url='https://api.example.com/items' source=app_default max_retries=3
DEBUG retry_policy_resolved method=DELETE url='https://api.example.com/x' source=hardcoded_fallback max_retries=0
```

---

### 3 — `RequestWorker.__init__` — forwarding log

**File**: `pypost/core/worker.py`

```python
logger.debug(
    "RequestWorker: default_retry_policy_injected=%s max_retries=%s",
    default_retry_policy is not None,
    default_retry_policy.max_retries if default_retry_policy is not None else "N/A",
)
```

Emitted at worker construction so that the DI chain is fully traceable from
`tabs_presenter` → `RequestWorker` → `RequestService`. Mirrors the existing
`alert_manager_injected` log added in PYPOST-418.

---

## Existing Observability (unchanged)

The following log events were already present and remain sufficient for their respective
paths:

| Event key | Level | Location | Purpose |
|-----------|-------|----------|---------|
| `http_attempt` | DEBUG | `_execute_http_with_retry` | Per-attempt method/url/attempt/max_retries |
| `retryable_status` | WARNING | `_execute_http_with_retry` | Retryable HTTP status code encountered |
| `retryable_error` | WARNING | `_execute_http_with_retry` | Retryable exception encountered |
| `retry_backoff` | DEBUG | `_execute_http_with_retry` | Back-off wait duration per attempt |
| `retry_cancelled_during_backoff` | DEBUG | `_execute_http_with_retry` | Stop flag raised during back-off |
| `retry_exhausted` | WARNING | `_emit_exhaustion_alert` | All retries consumed; alert emitted |

Metrics calls (`track_retry_attempt`, `track_email_notification_failure`) were also
already in place and remain unchanged.

---

## No Changes Required

- No new metrics counters added — `track_retry_attempt` already captures retry activity.
- No alerting changes — `_emit_exhaustion_alert` already fires via `AlertManager`.
- No changes to tests — the new log lines emit at DEBUG and do not affect assertions.
