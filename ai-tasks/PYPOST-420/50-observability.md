# PYPOST-420 — Observability

> Senior Engineer: senior_engineer
> Date: 2026-03-26
> Sprint: 167

---

## 1. Pre-existing Instrumentation

Before this step the following log events already existed in
`pypost/core/alert_manager.py`, emitted via the module-level logger
(`pypost.core.alert_manager`):

| Event key | Level | Where | What it signals |
|-----------|-------|-------|-----------------|
| `alert_emitted` | WARNING | `emit()` | Every structured alert written to the rotating log and optionally dispatched to webhook |
| `alert_webhook_failed` | WARNING | `_send_webhook()` | Webhook POST failed (network error, timeout, etc.) |

Both events include enough structured context to grep for in application logs.

---

## 2. Observability Gaps Found

| Gap | Risk |
|-----|------|
| Handler-guard eviction path was silent | No operator visibility when an `AlertManager` was GC'd without `close()` — the core bug this ticket fixes would be undetectable in production without this signal |
| Webhook success was dark | Could not confirm delivery without external monitoring |
| Lifecycle (`__init__` / `close()`) had no traces | Hard to correlate alert activity with instance churn in DEBUG mode |

---

## 3. Changes Made

All changes are in `pypost/core/alert_manager.py` using the module-level
`logger = logging.getLogger(__name__)`.  No new dependencies were introduced.

### 3.1 Stale-handler eviction warning (`__init__`)

```python
stale_handlers = list(self._logger.handlers)
if stale_handlers:
    logger.warning(
        "alert_manager_stale_handlers_evicted count=%d log_path=%s"
        " — prior AlertManager was not closed; evicting to prevent accumulation",
        len(stale_handlers),
        resolved,
    )
```

- **Level**: WARNING — this event means a previous `AlertManager` was discarded without
  calling `close()`, which is the exact bug PYPOST-420 fixes. In production this should
  never fire; if it does it signals a regression.
- **Includes**: handler count and log path to make the message self-contained for log
  aggregators.

### 3.2 Initialisation trace (`__init__`)

```python
logger.debug("alert_manager_init log_path=%s webhook=%s", resolved,
             "yes" if webhook_url else "no")
```

- **Level**: DEBUG — routine operational detail, suppressed in production unless
  `DEBUG` logging is enabled.
- **Includes**: resolved log path and whether a webhook target is configured.

### 3.3 Close trace (`close()`)

```python
logger.debug("alert_manager_close logger=%s", self._logger.name)
```

- **Level**: DEBUG — lifecycle event.
- **Includes**: the per-instance logger name (which encodes the memory address), useful
  for correlating `alert_manager_init` / `alert_manager_close` pairs under DEBUG.

### 3.4 Webhook success trace (`_send_webhook()`)

```python
resp = requests.post(...)
logger.debug("alert_webhook_ok url=%r status=%d", self._webhook_url, resp.status_code)
```

- **Level**: DEBUG — delivery confirmation; noisy in production, but available for
  targeted debugging without code changes.
- **Includes**: URL and HTTP status code. Non-2xx responses are not treated as errors
  by the current implementation (upstream decision, unchanged by this ticket).

---

## 4. Log-Event Inventory (complete)

| Event key | Level | Trigger condition |
|-----------|-------|-------------------|
| `alert_manager_init` | DEBUG | Every successful `AlertManager.__init__` |
| `alert_manager_stale_handlers_evicted` | WARNING | `__init__` finds leftover handlers (id() reuse) |
| `alert_emitted` | WARNING | Every `emit()` call |
| `alert_webhook_ok` | DEBUG | Webhook POST succeeds |
| `alert_webhook_failed` | WARNING | Webhook POST raises an exception |
| `alert_manager_close` | DEBUG | Every `close()` call |

---

## 5. Test Coverage of New Events

The existing regression tests in `TestAlertManagerAccumulation` exercise the stale-handler
path at runtime:

- `test_no_accumulation_via_gc_id_reuse` — CPython `id()` reuse forces the guard to run;
  the new `alert_manager_stale_handlers_evicted` WARNING fires and is visible in pytest
  live-log output, confirming the instrument is wired correctly.

No new tests were required: the observability additions are thin logging calls with no
branching logic of their own.

---

## 6. Operator Guidance

| Scenario | What to look for |
|----------|-----------------|
| Confirm an alert was processed | `grep alert_emitted app.log` |
| Investigate missing webhook delivery | `grep alert_webhook_failed app.log` |
| Check if accumulation bug regressed | `grep alert_manager_stale_handlers_evicted app.log` — any hit is actionable |
| Trace full lifecycle in a debug session | Enable DEBUG on `pypost.core.alert_manager` and look for `alert_manager_init` / `alert_manager_close` pairs |
