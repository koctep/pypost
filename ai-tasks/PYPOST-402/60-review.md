# Tech Debt Review: PYPOST-402 — Add Retry and Alerting for Email Failures

**Reviewer:** Team Lead
**Date:** 2026-03-24

---

## Summary

The implementation is functionally complete and all acceptance criteria are satisfied at the unit
test level. However, three wiring gaps mean that key features configured via the Settings UI never
reach the running application. Additionally, there are minor code hygiene issues that carry future
maintenance risk.

---

## Critical Issues

### TD-1: `AlertManager` never injected into `RequestWorker` ([PYPOST-418](https://pypost.atlassian.net/browse/PYPOST-418))

**File:** `pypost/core/worker.py` — `RequestWorker.__init__`

`RequestWorker` constructs `RequestService` directly without passing an `AlertManager`:

```python
self.service = RequestService(metrics=metrics, history_manager=history_manager,
                              template_service=template_service)
```

`RequestService` supports `alert_manager` via DI, and unit tests verify the path, but the
production call-site never supplies one. As a result, alerts are never emitted in a running
application regardless of settings.

**Impact:** FR-4 / AC-6 pass in isolated unit tests but are dead code in production.
**Fix:** `RequestWorker` must accept `alert_manager: AlertManager | None = None` and pass it
through to `RequestService`.

---

### TD-2: `AppSettings.default_retry_policy` is persisted but never applied ([PYPOST-419](https://pypost.atlassian.net/browse/PYPOST-419))

**Files:** `pypost/models/settings.py`, `pypost/core/worker.py`

The `SettingsDialog` saves a `default_retry_policy` to `AppSettings`. Neither `RequestWorker`
nor `RequestService` reads this field. Requests without a per-request `retry_policy` always
fall back to `max_retries=0` regardless of what the user configured.

**Impact:** AC-9 is partially satisfied (UI saves correctly) but the saved policy has no runtime
effect.
**Fix:** `TabsPresenter` (or `RequestWorker`) must resolve the effective retry policy before
execution: use `request.retry_policy` if set, otherwise fall back to
`settings.default_retry_policy`.

---

## Significant Issues

### TD-3: Logger accumulation in `AlertManager` ([PYPOST-420](https://pypost.atlassian.net/browse/PYPOST-420))

**File:** `pypost/core/alert_manager.py`

`AlertManager.__init__` creates a uniquely-named logger per instance:

```python
self._logger = logging.getLogger(f"pypost.alerts.{id(self)}")
```

Python's `logging.Manager` holds strong references to all named loggers indefinitely. Each
`AlertManager` construction (e.g., on every settings save) leaks one logger object, one
`RotatingFileHandler`, and an open file handle. The handler is never explicitly closed.

**Impact:** File handle leak on repeated settings changes; grows unbounded in long sessions.
**Fix:** Use a stable name (`"pypost.alerts"`) and manage handler lifecycle in a `close()` method
or replace the private logger with a `RotatingFileHandler` written to directly.

---

### TD-4: Bare `assert` in production retry path ([PYPOST-421](https://pypost.atlassian.net/browse/PYPOST-421))

**File:** `pypost/core/request_service.py:183`

```python
assert last_error is not None
```

Python assertions are silently disabled when the interpreter runs with `-O` or `-OO`. If this
branch is ever reached with `last_error = None`, the subsequent `raise last_error` would raise
`TypeError: exceptions must derive from BaseException` — an opaque crash with no useful context.

**Impact:** Defensive guard becomes a silent `TypeError` under optimised builds.
**Fix:** Replace with an explicit guard:
```python
if last_error is None:
    raise RuntimeError("retry loop exhausted with no recorded error")
```

---

## Minor Issues

### TD-5: `email_notification_failures_total` metric name is misleading ([PYPOST-422](https://pypost.atlassian.net/browse/PYPOST-422))

**File:** `pypost/core/metrics.py`

The counter fires for *any* request that exhausts all retries, not specifically email
notifications. The name implies a domain-specific scope that does not match the implementation
and will confuse dashboard consumers.

**Suggestion:** Rename to `request_retry_exhaustions_total{endpoint}` or add a note in the
metric description clarifying the broader scope.

---

### TD-6: `retryable_codes_edit` silently drops invalid input ([PYPOST-423](https://pypost.atlassian.net/browse/PYPOST-423))

**File:** `pypost/ui/dialogs/settings_dialog.py` — `_parse_retryable_codes()`

Non-digit tokens are silently ignored. A user who types `"429 503"` (space-separated) ends up
with an empty list; there is no UI feedback.

**Suggestion:** Validate on `accept()` and show an error message if any token is non-numeric,
or at least normalise whitespace before splitting.

---

### TD-7: `request_timeout` spin box created but never added to form layout ([PYPOST-424](https://pypost.atlassian.net/browse/PYPOST-424))

**File:** `pypost/ui/dialogs/settings_dialog.py`

`self.timeout_spin` is constructed and read in `accept()`, but the `addRow` call for it is
absent from the form. Users cannot change the request timeout from the settings dialog.

**Suggestion:** Add `self.form_layout.addRow("Request Timeout (seconds):", self.timeout_spin)`.

---

## Acceptance Criteria Status

| AC | Status | Notes |
|----|--------|-------|
| AC-1 | Pass | Unit-tested; runtime depends on TD-2 being resolved |
| AC-2 | Pass | Signal emitted correctly |
| AC-3 | Pass | `stop_flag` polled in backoff loop |
| AC-4 | Pass | `track_retry_attempt` called per attempt |
| AC-5 | Pass | `track_email_notification_failure` called on exhaustion |
| AC-6 | **Broken in production** | TD-1: `AlertManager` never injected |
| AC-7 | Pass | `retry_policy=None` path unchanged |
| AC-8 | Pass | 44 tests pass; ≥ 90 % branch coverage on retry/alert code |
| AC-9 | **Partially broken** | TD-2: settings saved but not applied |

---

## Linked Jira Items

| Key | Description | Priority |
|-----|-------------|----------|
| PYPOST-402-TD1 | Wire `AlertManager` into `RequestWorker` | High |
| PYPOST-402-TD2 | Apply `default_retry_policy` from `AppSettings` at runtime | High |
| PYPOST-402-TD3 | Fix `AlertManager` logger/handler leak | Medium |
| PYPOST-402-TD4 | Replace bare `assert` with explicit guard | Low |
| PYPOST-402-TD5 | Rename `email_notification_failures_total` | Low |
| PYPOST-402-TD6 | Validate `retryable_codes_edit` input | Low |
| PYPOST-402-TD7 | Add missing `request_timeout` row in settings form | Low |
