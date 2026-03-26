# PYPOST-418 — Architecture: AlertManager Injection into RequestWorker

> Senior Engineer: 2026-03-26
> Jira: PYPOST-418
> Status: Draft

---

## 1. Overview

`AlertManager` is fully implemented but never wired into the running application.
The fix is a pure dependency-injection plumbing task: create one `AlertManager`
instance at bootstrap and propagate it through the existing call chain without
changing any business logic.

**Injection chain:**

```
main.py
  └─ AlertManager(log_path, webhook_url, webhook_auth_header)   ← new
       └─ MainWindow(alert_manager=...)                          ← new param
            └─ TabsPresenter(alert_manager=...)                  ← new param
                 └─ RequestWorker(alert_manager=...)             ← new param
                      └─ RequestService(alert_manager=...)       ← already exists
```

---

## 2. Current State

| File | Gap |
|---|---|
| `main.py` | No `AlertManager` creation |
| `MainWindow.__init__` | No `alert_manager` param |
| `TabsPresenter.__init__` | No `alert_manager` param; no `self._alert_manager` |
| `TabsPresenter._handle_send_request` | `RequestWorker` built without `alert_manager` |
| `RequestWorker.__init__` | No `alert_manager` param; `RequestService` created without it |
| `RequestService.__init__` | Already accepts `alert_manager: AlertManager \| None = None` ✓ |
| `AppSettings` | Has `alert_webhook_url`, `alert_webhook_auth_header` but no `alert_log_path` |

---

## 3. Config Extension

### 3.1  `pypost/models/settings.py`

Add one field:

```python
alert_log_path: Optional[str] = None
```

This covers FR-1's `alerts.log_path` config key. A `None` value triggers
`AlertManager`'s built-in default (`~/.local/share/pypost/pypost-alerts.log`
via `platformdirs.user_data_dir`), so no functional change for existing users.

---

## 4. Bootstrap Changes

### 4.1  `pypost/main.py`

After `settings = config_manager.load_config()`, construct `AlertManager`:

```python
from pathlib import Path
from pypost.core.alert_manager import AlertManager

log_path = Path(settings.alert_log_path) if settings.alert_log_path else None
alert_manager = AlertManager(
    log_path=log_path,
    webhook_url=settings.alert_webhook_url,
    webhook_auth_header=settings.alert_webhook_auth_header,
)
```

Pass it into `MainWindow`:

```python
window = MainWindow(
    metrics=metrics_manager,
    template_service=template_service,
    config_manager=config_manager,
    alert_manager=alert_manager,       # ← new
)
```

The `alert_manager` instance is NOT closed at process exit (the OS reclaims
file handles). Adding explicit `alert_manager.close()` before `sys.exit` is
acceptable but out-of-scope for this ticket.

---

## 5. UI Layer Changes

### 5.1  `pypost/ui/main_window.py` — `MainWindow.__init__`

Extend the signature:

```python
def __init__(
    self,
    metrics: MetricsManager,
    template_service: TemplateService,
    config_manager: ConfigManager | None = None,
    alert_manager: AlertManager | None = None,   # ← new
) -> None:
```

Store and forward:

```python
self._alert_manager = alert_manager
```

Pass it to `TabsPresenter`:

```python
self.tabs = TabsPresenter(
    self.request_manager, self.state_manager, self.settings,
    metrics=self.metrics,
    history_manager=self.history_manager,
    template_service=self.template_service,
    alert_manager=self._alert_manager,   # ← new
)
```

Import addition at top of file:

```python
from pypost.core.alert_manager import AlertManager
```

### 5.2  `pypost/ui/presenters/tabs_presenter.py` — `TabsPresenter`

**`__init__` signature** (extend after `template_service`):

```python
def __init__(
    self,
    request_manager: RequestManager,
    state_manager: StateManager,
    settings: AppSettings,
    metrics: MetricsManager | None = None,
    history_manager: HistoryManager | None = None,
    template_service: TemplateService | None = None,
    alert_manager: AlertManager | None = None,   # ← new
    parent: QObject | None = None,
) -> None:
```

Store inside `__init__` body (alongside existing `self._template_service`):

```python
self._alert_manager = alert_manager
```

**`_handle_send_request`** — extend the `RequestWorker` construction:

```python
worker = RequestWorker(
    request_data,
    variables=self._current_variables,
    metrics=self._metrics,
    history_manager=self._history_manager,
    collection_name=collection_name,
    template_service=self._template_service,
    alert_manager=self._alert_manager,   # ← new
)
```

Import addition:

```python
from pypost.core.alert_manager import AlertManager
```

---

## 6. Worker Layer Changes

### 6.1  `pypost/core/worker.py` — `RequestWorker.__init__`

**Signature** (add after `template_service`):

```python
def __init__(
    self,
    request_data: RequestData,
    variables: dict = None,
    metrics: MetricsManager | None = None,
    history_manager: HistoryManager | None = None,
    collection_name: str | None = None,
    template_service: TemplateService | None = None,
    alert_manager: AlertManager | None = None,   # ← new
):
```

**Forward to `RequestService`**:

```python
self.service = RequestService(
    metrics=metrics,
    history_manager=history_manager,
    template_service=template_service,
    alert_manager=alert_manager,   # ← new
)
```

Import addition:

```python
from pypost.core.alert_manager import AlertManager
```

---

## 7. No Changes Required

| File | Reason |
|---|---|
| `pypost/core/request_service.py` | Already accepts `alert_manager`; `_emit_exhaustion_alert` already uses it |
| `pypost/core/alert_manager.py` | PYPOST-420 landed; no further changes needed |
| `pypost/models/errors.py` | Unchanged |
| `pypost/models/retry.py` | Unchanged |

---

## 8. Test Plan

### 8.1  `tests/test_worker.py` — new test class `TestRequestWorkerAlertManagerInjection`

| Test | Assertion |
|---|---|
| `test_alert_manager_forwarded_to_service` | When `RequestWorker(req, alert_manager=mock_am)` is constructed, `worker.service._alert_manager is mock_am` |
| `test_alert_manager_none_by_default` | When constructed without `alert_manager`, `worker.service._alert_manager is None` |

### 8.2  `tests/test_tabs_presenter.py` — new test class `TestTabsPresenterAlertManagerPropagation`

| Test | Assertion |
|---|---|
| `test_alert_manager_passed_to_worker` | When `TabsPresenter` has `_alert_manager=mock_am`, the `RequestWorker` constructed in `_handle_send_request` receives `alert_manager=mock_am`; verified by patching `RequestWorker.__init__` and capturing `kwargs` |
| `test_no_alert_manager_no_exception` | When `TabsPresenter` has `_alert_manager=None`, `_handle_send_request` completes without raising |

### 8.3  Regression: no changes to existing tests

- All 17 `test_alert_manager.py` tests must pass unchanged.
- All `test_retry.py` exhaustion-alert tests must pass unchanged.
- All existing `test_worker.py` tests must pass unchanged.

---

## 9. File Change Summary

| File | Change Type | Lines Affected (est.) |
|---|---|---|
| `pypost/models/settings.py` | Add field | +1 |
| `pypost/main.py` | Add AlertManager bootstrap + pass to MainWindow | +8 |
| `pypost/ui/main_window.py` | Add param, store, forward to TabsPresenter | +4 |
| `pypost/ui/presenters/tabs_presenter.py` | Add param, store, forward to RequestWorker | +4 |
| `pypost/core/worker.py` | Add param, forward to RequestService | +3 |
| `tests/test_worker.py` | New test class (2 tests) | +25 |
| `tests/test_tabs_presenter.py` | New test class (2 tests) | +35 |

Total estimated delta: ~80 lines, all additive.

---

## 10. Acceptance Criteria Traceability

| AC | Covered By |
|---|---|
| AC-1 — Single `AlertManager` at startup | §4.1 (main.py bootstrap) |
| AC-2 — `RequestWorker.__init__` signature | §6.1 |
| AC-3 — `RequestService` receives `alert_manager` | §6.1 (forwarded in `RequestService(...)`) |
| AC-4 — `TabsPresenter._handle_send_request` passes `alert_manager` | §5.2 |
| AC-5 — `None` raises no exception | All params default to `None`; existing `if self._alert_manager:` guard in `RequestService` |
| AC-6 — New tests; regressions pass | §8 |
| AC-7 — `_emit_exhaustion_alert` fires in live run | AC-1 + AC-3 together ensure the live path is wired |
