# PYPOST-378: Developer Documentation — TemplateService DI Chain

## What Changed

PYPOST-378 completes the `TemplateService` dependency-injection chain that was partially
introduced in PYPOST-45. Before this ticket, `TemplateService` instances were created silently
as internal fallbacks inside `HTTPClient`, `RequestService`, and `MCPServerImpl`. The
composition root (`main.py`) never created one, so the injection contract was never fulfilled.

This ticket:
1. Creates a single `TemplateService` instance in `main.py`.
2. Threads that instance through every constructor between the root and the leaf consumers.
3. Removes all internal `TemplateService()` fallback constructions.

---

## Injection Chain

```
main.py  →  TemplateService()   ← single instance, created here
  └─ MainWindow(template_service=ts)
       ├─ MCPServerManager(template_service=ts)
       │    └─ MCPServerImpl(template_service=ts)
       │         └─ RequestService(template_service=ts)
       │              └─ HTTPClient(template_service=ts)
       └─ TabsPresenter(template_service=ts)
            └─ RequestWorker(template_service=ts)   ← one per request
                 └─ RequestService(template_service=ts)
                      └─ HTTPClient(template_service=ts)
```

All `id()` values at every hop are identical — confirming a single shared instance.

---

## Files Modified

| File | Nature of Change |
|------|-----------------|
| `pypost/main.py` | Create `TemplateService()` once; pass to `MainWindow`; log at INFO |
| `pypost/ui/main_window.py` | Accept `template_service: TemplateService`; store; propagate |
| `pypost/core/mcp_server.py` | Accept `template_service: TemplateService | None = None`; propagate to `MCPServerImpl` |
| `pypost/core/mcp_server_impl.py` | Remove `else: TemplateService()` fallback; assign directly |
| `pypost/core/worker.py` | Accept `template_service: TemplateService | None = None`; pass to `RequestService` |
| `pypost/core/request_service.py` | Remove `else: TemplateService()` fallback; assign directly |
| `pypost/core/http_client.py` | Remove `else: TemplateService()` fallback; assign directly |
| `pypost/ui/presenters/tabs_presenter.py` | Accept `template_service`; store; pass to `RequestWorker` |
| `tests/test_http_client.py` | Inject `TemplateService()` in setUp; rewrite fallback-behaviour test |
| `tests/test_request_service.py` | Inject `TemplateService()` in setUp; rewrite fallback-behaviour test |

---

## Constructor Signatures (after this ticket)

```python
# main.py
template_service = TemplateService()
MainWindow(metrics=metrics_manager, template_service=template_service)

# MainWindow
def __init__(self, metrics: MetricsManager, template_service: TemplateService) -> None

# MCPServerManager
def __init__(self, metrics: MetricsManager | None = None,
             template_service: TemplateService | None = None)

# MCPServerImpl
def __init__(self, name="pypost", metrics=None, template_service: TemplateService | None = None)

# RequestWorker
def __init__(self, request_data, variables=None, metrics=None,
             history_manager=None, collection_name=None,
             template_service: TemplateService | None = None)

# RequestService
def __init__(self, metrics=None, history_manager=None,
             template_service: TemplateService | None = None)

# HTTPClient
def __init__(self, metrics=None, template_service: TemplateService | None = None)

# TabsPresenter
def __init__(self, request_manager, state_manager, settings,
             metrics=None, history_manager=None,
             template_service: TemplateService | None = None, parent=None)
```

---

## Writing Tests

### Tests that exercise template rendering

Inject a real `TemplateService()` (it is stateless and cheap):

```python
from pypost.core.template_service import TemplateService

svc = RequestService(metrics=MagicMock(), template_service=TemplateService())
```

### Tests that do NOT exercise rendering paths

Omit `template_service` (defaults to `None`). Calling a render path without injection will
raise `AttributeError` — this is intentional, as it surfaces missing injection early.

### Asserting the no-injection contract

```python
client = HTTPClient()
self.assertIsNone(client._template_service)  # no silent fallback
```

---

## Observability

Set the log level to `DEBUG` to trace the full injection chain at startup:

```
INFO  pypost.main               template_service_created id=<N>
DEBUG pypost.core.mcp_server    MCPServerManager: propagating TemplateService id=<N>
DEBUG pypost.core.mcp_server_impl MCPServerImpl: using injected TemplateService id=<N>
DEBUG pypost.core.request_service RequestService: using injected TemplateService id=<N>
DEBUG pypost.core.http_client   HTTPClient: using injected TemplateService id=<N>

# Per request:
DEBUG pypost.core.worker        RequestWorker: propagating TemplateService id=<N>
DEBUG pypost.core.request_service RequestService: using injected TemplateService id=<N>
DEBUG pypost.core.http_client   HTTPClient: using injected TemplateService id=<N>
```

All `id` values must be identical to confirm a single shared instance is in use.

---

## Related Tickets

| Ticket | Description |
|--------|-------------|
| PYPOST-44 | `MetricsManager` singleton → constructor injection (completed, same pattern) |
| PYPOST-45 | `template_service` global removed; partial injection introduced |
| PYPOST-378 | This ticket — completes the injection chain |
| PYPOST-49 | Future: split `MetricsManager` into `MetricsRegistry` + `MetricsServer` |
