# PYPOST-419 — Architecture

## Summary

Wire `AppSettings.default_retry_policy` into `RequestService` via the existing DI chain so the
policy resolution order becomes: per-request > app default > hardcoded fallback.

---

## Scope of Changes

| File | Change |
|------|--------|
| `pypost/core/request_service.py` | Add `default_retry_policy` constructor param; fallback in `_execute_http_with_retry` |
| `pypost/core/worker.py` | Add `default_retry_policy` constructor param; thread it to `RequestService` |
| `pypost/ui/presenters/tabs_presenter.py` | Pass `self._settings.default_retry_policy` when constructing `RequestWorker` |
| `tests/test_request_service.py` | Add `TestRequestServiceRetryPolicyResolution` with three branch tests |

No changes to: `RetryPolicy`, `AppSettings`, `ConfigManager`, `SettingsDialog`, or any other file.

---

## Design Decisions

### 1 — Inject `Optional[RetryPolicy]`, not full `AppSettings`

`RequestService` is a pure service layer; it must not depend on the top-level `AppSettings` model.
Passing only `Optional[RetryPolicy]` keeps the interface minimal (FR-1), avoids coupling the
service to the settings schema, and requires no new import.

### 2 — Single fallback point inside `_execute_http_with_retry`

The fallback is applied once at the top of `_execute_http_with_retry` before any values are
unpacked from `policy`. This is the only place where `request.retry_policy` is currently read,
so adding two lines here satisfies FR-2 without touching any other code path.

### 3 — `RequestWorker` forwards the resolved value, not a live settings reference

`RequestWorker` receives `default_retry_policy: Optional[RetryPolicy]` as a constructor argument
(not `AppSettings`). The caller (`tabs_presenter`) extracts the value at instantiation time. This
is consistent with how `alert_manager` was wired in PYPOST-418 and avoids giving the worker a
mutable settings handle.

---

## Detailed Changes

### `pypost/core/request_service.py`

**Constructor** — add one parameter:

```python
def __init__(
    self,
    metrics: MetricsManager | None = None,
    template_service: TemplateService | None = None,
    history_manager: HistoryManager | None = None,
    alert_manager: AlertManager | None = None,
    default_retry_policy: RetryPolicy | None = None,   # NEW
) -> None:
    ...
    self._default_retry_policy = default_retry_policy  # NEW
```

**`_execute_http_with_retry`** — insert fallback after the existing `policy` assignment (line 107):

```python
# Before (lines 107-111):
policy: RetryPolicy | None = request.retry_policy
max_retries = policy.max_retries if policy else 0
delay = policy.retry_delay_seconds if policy else 1.0
multiplier = policy.retry_backoff_multiplier if policy else 2.0
retryable_codes = set(policy.retryable_status_codes) if policy else set()

# After:
policy: RetryPolicy | None = request.retry_policy
if policy is None:
    policy = self._default_retry_policy   # NEW — app-level default fallback
max_retries = policy.max_retries if policy else 0
delay = policy.retry_delay_seconds if policy else 1.0
multiplier = policy.retry_backoff_multiplier if policy else 2.0
retryable_codes = set(policy.retryable_status_codes) if policy else set()
```

The two existing lines of debug logging (`http_attempt`) already log `max_retries`, so the
resolved policy value is observable without additional log changes.

### `pypost/core/worker.py`

**Constructor** — add one parameter after `alert_manager`:

```python
def __init__(
    self,
    request_data: RequestData,
    variables: dict = None,
    metrics: MetricsManager | None = None,
    history_manager: HistoryManager | None = None,
    collection_name: str | None = None,
    template_service: TemplateService | None = None,
    alert_manager: AlertManager | None = None,
    default_retry_policy: RetryPolicy | None = None,   # NEW
):
    ...
    self.service = RequestService(
        metrics=metrics,
        history_manager=history_manager,
        template_service=template_service,
        alert_manager=alert_manager,
        default_retry_policy=default_retry_policy,     # NEW
    )
```

Import `RetryPolicy` at the top of `worker.py` (it is already imported in `request_service.py`;
`worker.py` needs its own import for the type annotation):

```python
from pypost.models.retry import RetryPolicy
```

### `pypost/ui/presenters/tabs_presenter.py`

In `send_request` (the `RequestWorker(...)` construction block, ~line 352):

```python
worker = RequestWorker(
    request_data,
    variables=self._current_variables,
    metrics=self._metrics,
    history_manager=self._history_manager,
    collection_name=collection_name,
    template_service=self._template_service,
    alert_manager=self._alert_manager,
    default_retry_policy=self._settings.default_retry_policy,   # NEW
)
```

`self._settings` is already stored on the presenter (set in `__init__` and updated in
`apply_settings`). No structural changes needed.

---

## Test Plan

New class `TestRequestServiceRetryPolicyResolution` in `tests/test_request_service.py`.

All three tests use `RequestService` directly, mock `http_client.send_request`, and assert on
the number of calls or the response behaviour.

### Test 1 — per-request policy wins (AC-2)

```
RequestService(default_retry_policy=RetryPolicy(max_retries=5))
request.retry_policy = RetryPolicy(max_retries=1)
http_client returns status 500 on every call

→ http_client.send_request called exactly 2 times (1 initial + 1 retry)
```

### Test 2 — app default used when no per-request policy (AC-1)

```
RequestService(default_retry_policy=RetryPolicy(max_retries=2, retryable_status_codes=[500]))
request.retry_policy = None
http_client returns status 500 on every call

→ http_client.send_request called exactly 3 times (1 initial + 2 retries)
```

### Test 3 — hardcoded fallback when both are None (AC-3)

```
RequestService()  # no default_retry_policy
request.retry_policy = None
http_client returns status 500 on every call

→ http_client.send_request called exactly 1 time (max_retries=0, no retries)
```

**Existing tests**: no modifications required. `RequestService()` with no args still works
because `default_retry_policy=None` defaults to the current hardcoded behaviour (AC-3, AC-4).

---

## Policy Resolution Logic (pseudocode)

```
effective_policy = request.retry_policy
                   or self._default_retry_policy
                   or None          # → hardcoded defaults kick in
```

Expressed as the two-line insert into `_execute_http_with_retry`:

```python
policy: RetryPolicy | None = request.retry_policy
if policy is None:
    policy = self._default_retry_policy
```

---

## Backward Compatibility

- All existing callers of `RequestService(...)` and `RequestWorker(...)` continue to work
  unchanged; the new parameter is keyword-only and defaults to `None`.
- `AppSettings` files without `default_retry_policy` deserialise with `None` (Pydantic default).
- No migration, no UI change, no model schema change.

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| `RequestWorker` constructor signature clash with PYPOST-418 `alert_manager` | Low | New param added after `alert_manager`; call site uses keyword args |
| Test breakage from added constructor param | None | Default=None preserves existing call signatures |
| Retry counts logged inaccurately | None | `max_retries` is derived from the already-resolved `policy` |
