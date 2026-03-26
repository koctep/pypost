# PYPOST-418 — Developer Documentation

> Team Lead: 2026-03-26
> Jira: PYPOST-418

---

## 1. Overview

PYPOST-418 wires `AlertManager` into the live application for the first time.
Before this change, `AlertManager` was fully implemented but never injected into
`RequestWorker`, so all retry-exhaustion alert callbacks were silently dead in
production. This ticket adds the dependency-injection plumbing across five layers
without altering any business logic.

---

## 2. Architecture: The DI Chain

```
main.py
  └─ AlertManager(log_path, webhook_url, webhook_auth_header)   ← created once
       └─ MainWindow(alert_manager=...)
            └─ TabsPresenter(alert_manager=...)
                 └─ RequestWorker(alert_manager=...)            ← per request
                      └─ RequestService(alert_manager=...)      ← pre-existing wiring
```

`RequestService._emit_exhaustion_alert()` was already implemented and guarded on
`self._alert_manager is not None`; this ticket simply ensures that guard is no
longer always `False` in production.

---

## 3. Configuration

`AlertManager` is configured via `AppSettings` fields (stored in the user config file):

| Field | Type | Default | Description |
|---|---|---|---|
| `alert_log_path` | `Optional[str]` | `None` | Absolute path to the alert log file. `None` uses the platform default (`~/.local/share/pypost/pypost-alerts.log`). |
| `alert_webhook_url` | `Optional[str]` | `None` | Webhook URL for alert delivery. `None` disables webhook delivery. |
| `alert_webhook_auth_header` | `Optional[str]` | `None` | Authorization header value for the webhook. Logged as a boolean (`set/not set`) — never in plain text. |

**Bootstrap logic (`main.py:34-44`):**

```python
log_path = Path(settings.alert_log_path) if settings.alert_log_path else None
alert_manager = AlertManager(
    log_path=log_path,
    webhook_url=settings.alert_webhook_url,
    webhook_auth_header=settings.alert_webhook_auth_header,
)
logger.info(
    "alert_manager_created log_path=%s webhook_url_set=%s",
    log_path,
    bool(settings.alert_webhook_url),
)
```

---

## 4. Changed Files

### 4.1 `pypost/models/settings.py`

Added field:

```python
alert_log_path: Optional[str] = None
```

Joins the two pre-existing alert fields (`alert_webhook_url`,
`alert_webhook_auth_header`). All three are optional with `None` defaults.

---

### 4.2 `pypost/main.py`

- Imports: `Path` (stdlib), `AlertManager`.
- Creates `AlertManager` after `config_manager.load_config()`, before `MainWindow`.
- Passes `alert_manager=alert_manager` to `MainWindow(...)`.
- Logs `alert_manager_created` at INFO level.

---

### 4.3 `pypost/ui/main_window.py`

Signature change:

```python
def __init__(
    self,
    metrics: MetricsManager,
    template_service: TemplateService,
    config_manager: ConfigManager | None = None,
    alert_manager: AlertManager | None = None,   # new
) -> None:
```

- Stores `self._alert_manager = alert_manager`.
- Passes `alert_manager=self._alert_manager` to `TabsPresenter(...)`.
- Logs `MainWindow: alert_manager_injected=<bool>` at DEBUG.

---

### 4.4 `pypost/ui/presenters/tabs_presenter.py`

Signature change:

```python
def __init__(
    self,
    request_manager: RequestManager,
    state_manager: StateManager,
    settings: AppSettings,
    metrics: MetricsManager | None = None,
    history_manager: HistoryManager | None = None,
    template_service: TemplateService | None = None,
    alert_manager: AlertManager | None = None,   # new
    parent: QObject | None = None,
) -> None:
```

- Stores `self._alert_manager = alert_manager`.
- In `_handle_send_request`, passes `alert_manager=self._alert_manager` to
  `RequestWorker(...)`.
- Logs `TabsPresenter: alert_manager_injected=<bool>` at DEBUG.

---

### 4.5 `pypost/core/worker.py`

Signature change:

```python
def __init__(
    self,
    request_data: RequestData,
    variables: dict = None,
    metrics: MetricsManager | None = None,
    history_manager: HistoryManager | None = None,
    collection_name: str | None = None,
    template_service: TemplateService | None = None,
    alert_manager: AlertManager | None = None,   # new
):
```

- Forwards `alert_manager` to `RequestService(...)`.
- Logs `RequestWorker: alert_manager_injected=<bool> id=<object-id>` at DEBUG.
  The `id=` field can be cross-referenced with the bootstrap log to confirm the
  same singleton is in use.

---

## 5. Observable Log Stream

At application startup and for each request, the following log sequence confirms
correct injection:

```
INFO  pypost.main                           alert_manager_created log_path=… webhook_url_set=True
DEBUG pypost.ui.main_window                 MainWindow: alert_manager_injected=True
DEBUG pypost.ui.presenters.tabs_presenter   TabsPresenter: alert_manager_injected=True
DEBUG pypost.core.worker                    RequestWorker: alert_manager_injected=True id=140…
```

Any `False` in this sequence identifies the broken link. The chain is:
`main.py` (creates) → `MainWindow` (forwards) → `TabsPresenter` (forwards) →
`RequestWorker` (forwards to `RequestService`).

**Debug logging** (`DEBUG` level) is off by default in production. Set
`PYPOST_LOG_LEVEL=DEBUG` (or adjust `logging.basicConfig` in `main.py`) to
enable the full injection trace.

---

## 6. Testing

### 6.1 New Tests

**`tests/test_worker.py` — `TestRequestWorkerAlertManagerInjection`**

| Test | What it checks |
|---|---|
| `test_alert_manager_forwarded_to_service` | `worker.service._alert_manager is mock_am` when `alert_manager=mock_am` is passed |
| `test_alert_manager_none_by_default` | `worker.service._alert_manager is None` when no `alert_manager` is passed |

**`tests/test_tabs_presenter.py` — `TestTabsPresenterAlertManagerPropagation`**

| Test | What it checks |
|---|---|
| `test_alert_manager_passed_to_worker` | `RequestWorker` receives `alert_manager=mock_am` when `TabsPresenter._alert_manager` is set; verified by patching `RequestWorker` and inspecting `call_args` kwargs |
| `test_no_alert_manager_no_exception` | `_handle_send_request` completes without raising when `_alert_manager=None` |

### 6.2 Running the Tests

```bash
pytest tests/ -v
# Expected: 274 passed, 0 failed
```

### 6.3 Regression Coverage

- All 17 `tests/test_alert_manager.py` tests pass unchanged.
- All `tests/test_retry.py` exhaustion-alert tests pass unchanged.
- All pre-existing `tests/test_worker.py` and `tests/test_tabs_presenter.py` tests
  pass unchanged.

---

## 7. Known Limitations / Carry-Forward

| Item | Tracking |
|---|---|
| `alert_manager.close()` not called at `sys.exit()` | PYPOST-433 |
| `alert_log_path` / webhook fields not exposed in Settings UI | Unregistered — low priority UX enhancement |
| No `AlertManager` health check or metrics counter | Out of scope; Prometheus metrics cover request-level observability |

---

## 8. Dependencies

| Ticket | Status | Notes |
|---|---|---|
| PYPOST-420 | Done (commit `a397a18`) | Fixes handler accumulation in `AlertManager`; must land before PYPOST-418 |
| PYPOST-419 | Blocked on PYPOST-418 | Retry policy changes; can proceed now |
