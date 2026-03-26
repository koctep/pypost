# PYPOST-418 — Observability

> Senior Engineer: 2026-03-26
> Jira: PYPOST-418

---

## 1. Goal

Ensure the AlertManager dependency-injection chain is observable at runtime so
operators can confirm the live path is wired and diagnose silent-injection failures
without resorting to source-code inspection.

---

## 2. Pre-existing Logging (not added by this ticket)

The following log lines already existed before PYPOST-418 landed and cover adjacent
concerns:

| Location | Log line | Level |
|---|---|---|
| `main.py` | `"PyPost starting up"` / `"PyPost shutting down"` | INFO |
| `worker.py` | `worker_run_started`, `worker_run_completed`, `worker_stop_requested` | DEBUG |
| `worker.py` | `RequestWorker: propagating TemplateService id=…` | DEBUG |
| `tabs_presenter.py` | `request_send_initiated method=… url=…` | INFO |
| `main_window.py` | `config_manager_source source=…`, `main_window_initialized` | DEBUG/INFO |

---

## 3. Observability Added by This Ticket

### 3.1  `pypost/main.py` — AlertManager bootstrap confirmation (INFO)

```python
logger.info(
    "alert_manager_created log_path=%s webhook_url_set=%s",
    log_path,
    bool(settings.alert_webhook_url),
)
```

**Why**: Operators need to see that `AlertManager` was successfully constructed at
startup and which sink (file / webhook) is active. Without this, a misconfigured
`alert_log_path` or absent webhook URL is invisible in the log stream.

**Fields**:
- `log_path` — resolved `Path` object (or `None` for platform default).
- `webhook_url_set` — boolean; avoids logging the raw URL/auth header in plain text.

---

### 3.2  `pypost/core/worker.py` — Per-request injection confirmation (DEBUG)

```python
logger.debug(
    "RequestWorker: alert_manager_injected=%s id=%s",
    alert_manager is not None,
    id(alert_manager) if alert_manager is not None else "None",
)
```

**Why**: Every `RequestWorker` instance receives (or does not receive) an
`AlertManager`. Without this log, a caller that accidentally passes `None` is
indistinguishable from a correctly wired caller when reviewing logs.  The `id=`
field allows cross-referencing with the bootstrap `id()` to confirm the same
singleton is propagated throughout.

---

### 3.3  `pypost/ui/main_window.py` — Injection confirmation at UI layer (DEBUG)

```python
logger.debug("MainWindow: alert_manager_injected=%s", alert_manager is not None)
```

**Why**: `MainWindow` is the first UI component in the injection chain. A debug
line here makes it easy to bisect injection failures — if this is `False`, the
bug is upstream in `main.py`; if `True`, the bug is downstream.

---

### 3.4  `pypost/ui/presenters/tabs_presenter.py` — Injection confirmation at presenter layer (DEBUG)

```python
logger.debug("TabsPresenter: alert_manager_injected=%s", alert_manager is not None)
```

**Why**: `TabsPresenter` is the component that creates `RequestWorker` per request.
Confirming injection here closes the observable chain:
`main.py → MainWindow → TabsPresenter → RequestWorker`.

---

## 4. Injection Chain Coverage

After this ticket, the full DI chain is observable in the log stream:

```
INFO  pypost.main          alert_manager_created log_path=… webhook_url_set=…
DEBUG pypost.ui.main_window MainWindow: alert_manager_injected=True
DEBUG pypost.ui.presenters.tabs_presenter TabsPresenter: alert_manager_injected=True
DEBUG pypost.core.worker   RequestWorker: alert_manager_injected=True id=140…
```

Any `False` in this sequence immediately identifies the broken link in the chain.

---

## 5. What Was Deliberately Not Added

| Candidate | Decision |
|---|---|
| Metrics counter for `alert_manager_present` | Out of scope — no metrics infra for boolean config flags |
| WARNING when `alert_manager is None` | Would be noisy in unit-test contexts; `None` is a valid state (tests, CI) |
| `alert_manager.close()` call at shutdown | Explicitly out of scope per architecture §4.1 |
| Health-check endpoint for AlertManager state | Out of scope; existing Prometheus metrics server covers request-level observability |

---

## 6. Test Impact

No new tests required for the log lines themselves (they are `debug`/`info` side-effects
with no branching logic). All 274 existing tests continue to pass.
