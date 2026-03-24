# Code Cleanup: PYPOST-402 — Add Retry and Alerting for Email Failures

## Summary

Implementation is complete. The following cleanup observations were made during review.

---

## Issues Found and Resolved

### 1. Missing exhaustion alert for exception-based retry exhaustion

**File:** `pypost/core/request_service.py`

**Issue:** The architecture's `_execute_http_with_retry` showed `_emit_exhaustion_alert` only in the
post-loop block. However, exception-based exhaustion raises inside the loop before reaching that
block, meaning the alert was never emitted.

**Fix:** `_emit_exhaustion_alert` is called before `raise last_error` in the `except ExecutionError`
branch when `attempt == max_retries`. This covers both exhaustion paths (status code and exception).

---

### 2. `httpx` not in requirements.txt

**File:** `pypost/core/alert_manager.py`

**Issue:** Architecture specified `httpx` for the webhook HTTP call, but `httpx` is not a listed
dependency. `requests` is already present.

**Fix:** Used `requests` instead of `httpx` throughout `AlertManager._send_webhook`. No new
dependency introduced.

---

### 3. `AppSettings` missing `default_retry_policy` field

**File:** `pypost/models/settings.py`

**Issue:** `SettingsDialog` reads and writes `current_settings.default_retry_policy`, but this field
was not initially included in `AppSettings`. The dialog would fail at runtime.

**Fix:** Added `default_retry_policy: Optional[RetryPolicy] = None` to `AppSettings`.

---

## Code Quality Checks

| Check | Status |
|-------|--------|
| Line length ≤ 100 chars | Pass |
| LF line endings | Pass |
| No trailing whitespace | Pass |
| Single final newline | Pass |
| All code/comments in English | Pass |
| Type hints present | Pass |
| No unused imports | Pass |
| PEP 8 compliance | Pass |

---

## Test Coverage

| File | New Tests | Result |
|------|-----------|--------|
| `tests/test_retry.py` | 22 | 22 pass |
| `tests/test_alert_manager.py` | 14 | 14 pass |
| `tests/test_worker.py` | +1 (retry signal) | Pass |

All 44 new/modified tests pass. Full suite: 187/191 pass (4 pre-existing failures unrelated to
this task: `test_history_manager` tmpdir cleanup race, `test_http_client_sse_probe` NoneType
template_service).

---

## Files Changed

| File | Type | Description |
|------|------|-------------|
| `pypost/models/retry.py` | New | `RetryPolicy` Pydantic model |
| `pypost/core/alert_manager.py` | New | `AlertPayload` + `AlertManager` (rotating log + webhook) |
| `pypost/models/models.py` | Modified | Added `retry_policy: Optional[RetryPolicy] = None` |
| `pypost/models/settings.py` | Modified | Added `default_retry_policy`, `alert_webhook_url`, `alert_webhook_auth_header` |
| `pypost/core/metrics.py` | Modified | 2 new counters + `track_retry_attempt`, `track_email_notification_failure` |
| `pypost/core/request_service.py` | Modified | `_execute_http_with_retry`, `_emit_exhaustion_alert`, DI for `AlertManager`, `retry_callback` param |
| `pypost/core/worker.py` | Modified | `retry_attempt` signal, `on_retry` callback wiring |
| `pypost/ui/presenters/tabs_presenter.py` | Modified | `retry_attempt` connected, `_on_retry_attempt` handler |
| `pypost/ui/dialogs/settings_dialog.py` | Modified | Retry policy fields + webhook fields UI |
| `tests/test_retry.py` | New | Retry logic unit tests |
| `tests/test_alert_manager.py` | New | AlertManager unit tests |
| `tests/test_worker.py` | Modified | Added `TestRequestWorkerRetrySignal` |
