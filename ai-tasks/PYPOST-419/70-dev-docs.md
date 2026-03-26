# PYPOST-419 — Developer Documentation

**Feature**: Wire `AppSettings.default_retry_policy` into `RequestService`
**Date**: 2026-03-26
**Sprint**: 167

---

## Overview

Prior to this change, `AppSettings.default_retry_policy` was persisted to disk and editable
via the Settings dialog, but `RequestService` never read it. Any request without an explicit
per-request `retry_policy` silently fell back to hardcoded defaults (`max_retries=0`), making
the user-facing retry configuration completely inert.

This change threads `default_retry_policy` through the existing DI chain and applies it as
the middle tier in the three-level policy resolution cascade.

---

## Policy Resolution Order

```
request.retry_policy          (per-request, highest priority)
    ↓ if None
self._default_retry_policy    (from AppSettings, user-configurable)
    ↓ if None
hardcoded defaults             (max_retries=0, delay=1.0s, multiplier=2.0)
```

The resolution happens once at the top of `_execute_http_with_retry` before any policy
values are unpacked:

```python
# pypost/core/request_service.py — _execute_http_with_retry
policy: RetryPolicy | None = request.retry_policy
if policy is None:
    policy = self._default_retry_policy
# Then: max_retries = policy.max_retries if policy else 0  ...
```

---

## DI Chain

```
AppSettings.default_retry_policy
    │
    ▼  (extracted at send time)
TabsPresenter._handle_send_request
    │  default_retry_policy=self._settings.default_retry_policy
    ▼
RequestWorker.__init__
    │  default_retry_policy=default_retry_policy
    ▼
RequestService.__init__
    │  self._default_retry_policy = default_retry_policy
    ▼
RequestService._execute_http_with_retry
    │  policy = request.retry_policy or self._default_retry_policy
    ▼
Effective RetryPolicy (applied to HTTP request loop)
```

---

## Files Changed

| File | Change |
|------|--------|
| `pypost/core/request_service.py` | Added `default_retry_policy: RetryPolicy | None = None` constructor param; stored as `self._default_retry_policy`; two-line fallback in `_execute_http_with_retry`; debug log at init and per-request |
| `pypost/core/worker.py` | Added `from pypost.models.retry import RetryPolicy` import; added `default_retry_policy` constructor param; forwarded to `RequestService`; debug log at init |
| `pypost/ui/presenters/tabs_presenter.py` | Passed `self._settings.default_retry_policy` when constructing `RequestWorker` in `_handle_send_request` |
| `tests/test_request_service.py` | Added `TestRequestServiceRetryPolicyResolution` with three branch tests (AC-1 / AC-2 / AC-3) |

---

## Constructor Signatures

### `RequestService`

```python
RequestService(
    metrics: MetricsManager | None = None,
    template_service: TemplateService | None = None,
    history_manager: HistoryManager | None = None,
    alert_manager: AlertManager | None = None,
    default_retry_policy: RetryPolicy | None = None,   # NEW
)
```

### `RequestWorker`

```python
RequestWorker(
    request_data: RequestData,
    variables: dict = None,
    metrics: MetricsManager | None = None,
    history_manager: HistoryManager | None = None,
    collection_name: str | None = None,
    template_service: TemplateService | None = None,
    alert_manager: AlertManager | None = None,
    default_retry_policy: RetryPolicy | None = None,   # NEW
)
```

All new parameters are keyword-only and default to `None`. All existing call sites are
backward-compatible without modification.

---

## Observability

Three debug-level log events were added to make the full DI chain traceable:

| Event key | Location | Fields |
|-----------|----------|--------|
| `RequestService: default_retry_policy_injected=...` | `RequestService.__init__` | `injected` (bool), `max_retries` (int or `N/A`) |
| `retry_policy_resolved ...` | `_execute_http_with_retry` | `method`, `url`, `source` (`per_request` / `app_default` / `hardcoded_fallback`), `max_retries` |
| `RequestWorker: default_retry_policy_injected=...` | `RequestWorker.__init__` | `injected` (bool), `max_retries` (int or `N/A`) |

**Example log sequence for a request using the app-level default:**

```
DEBUG RequestWorker: default_retry_policy_injected=True max_retries=3
DEBUG RequestService: default_retry_policy_injected=True max_retries=3
DEBUG retry_policy_resolved method=GET url='https://api.example.com/data' source=app_default max_retries=3
DEBUG http_attempt method=GET url='https://api.example.com/data' attempt=0 max_retries=3
WARNING retryable_status method=GET url='https://api.example.com/data' status=500 attempt=0 max_retries=3
...
```

Existing log events (`http_attempt`, `retryable_status`, `retryable_error`, `retry_backoff`,
`retry_exhausted`) were unchanged and remain authoritative for per-attempt retry activity.

---

## Snapshot Semantics

`default_retry_policy` is captured at `RequestWorker` construction time (i.e. when the user
clicks Send). A settings change while a request is in-flight does not affect that request.
The updated policy takes effect on the next Send action. This is consistent with how
`alert_manager` and `template_service` are handled.

---

## Test Coverage

```
tests/test_request_service.py::TestRequestServiceRetryPolicyResolution
    test_per_request_policy_wins_over_app_default      AC-2  PASS
    test_app_default_used_when_no_per_request_policy   AC-1  PASS
    test_hardcoded_fallback_when_both_policies_none    AC-3  PASS
```

All 26 tests in `test_request_service.py` pass. No existing tests were modified.

---

## Configuration

Users configure the application-level retry policy via **Settings → Retry Policy**. The
value is stored in `~/.config/pypost/settings.json` under `default_retry_policy` and
loaded by `ConfigManager` into `AppSettings` on startup. Old `settings.json` files that
omit this field deserialise with `default_retry_policy=None` (Pydantic default); no
migration is required.

---

## Related Issues

| Issue | Description | Status |
|-------|-------------|--------|
| PYPOST-420 | Fix handler accumulation in `AlertManager` | Closed (commit `a397a18`) |
| PYPOST-418 | Wire `AlertManager` into `RequestWorker` via DI | Closed (commit `39eb591`) |
| PYPOST-419 | Wire `default_retry_policy` into `RequestService` | **This issue** |
| PYPOST-402 | Parent epic — AlertManager / retry-wiring group | Updated |
