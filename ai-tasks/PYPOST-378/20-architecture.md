# PYPOST-378: Architecture — Complete TemplateService DI Chain

## Overview

This task completes the `TemplateService` dependency-injection chain that was partially introduced
in PYPOST-45. The composition root (`main.py`) must create exactly one `TemplateService` instance
and thread it through every constructor that needs it, eliminating all internal fallback
instantiations.

---

## Current State

### Injection chain (incomplete)

```
main.py                  — no TemplateService instantiation
  └─ MainWindow          — no TemplateService param
       ├─ MCPServerManager  — no TemplateService param
       │    └─ MCPServerImpl  — fallback: TemplateService()   ← violation
       │         └─ RequestService — fallback: TemplateService()  ← violation
       │              └─ HTTPClient — fallback: TemplateService() ← violation
       └─ TabsPresenter  — no TemplateService param
            └─ RequestWorker (constructed at tabs_presenter.py:316)
                 — no TemplateService param
                 └─ RequestService — fallback: TemplateService()  ← violation
                      └─ HTTPClient — fallback: TemplateService() ← violation
```

### Target state

```
main.py  →  TemplateService()   (single instance)
  └─ MainWindow(template_service=ts)
       ├─ MCPServerManager(template_service=ts)
       │    └─ MCPServerImpl(template_service=ts)
       │         └─ RequestService(template_service=ts)
       │              └─ HTTPClient(template_service=ts)
       └─ TabsPresenter(template_service=ts)
            └─ RequestWorker(template_service=ts)
                 └─ RequestService(template_service=ts)
                      └─ HTTPClient(template_service=ts)
```

---

## Design Decisions

### 1. No new abstractions
`TemplateService` is a concrete, stateless Jinja2 wrapper. Introducing a `TemplateServiceProtocol`
is explicitly out of scope (requirements note). Pass the concrete type throughout.

### 2. `| None = None` signature style preserved at leaf classes
`HTTPClient`, `RequestService`, and `MCPServerImpl` keep `template_service: TemplateService | None = None`
for test ergonomics, but remove the internal `TemplateService()` fallback creation. When `None`
is passed the attribute is set to `None`; callers in production always inject the real instance.

### 3. Minimal diff surface
Only the 8 files identified in the requirements are touched. No refactoring of unrelated code.

### 4. MetricsManager pattern followed exactly
`MetricsManager` was already injected correctly in PYPOST-44. The `TemplateService` chain should
mirror the same propagation pattern: created once in `main.py`, passed to `MainWindow`, threaded
downward via constructors.

---

## File-by-File Changes

### `pypost/main.py`

**Change:** Import `TemplateService`, create one instance, pass to `MainWindow`.

```python
# add import
from pypost.core.template_service import TemplateService

# inside main():
template_service = TemplateService()

window = MainWindow(metrics=metrics_manager, template_service=template_service)
```

---

### `pypost/ui/main_window.py`

**Change:** Accept `template_service: TemplateService` parameter, store it, propagate to
`MCPServerManager` and `TabsPresenter`.

```python
# add import
from pypost.core.template_service import TemplateService

class MainWindow(QMainWindow):
    def __init__(self, metrics: MetricsManager, template_service: TemplateService) -> None:
        ...
        self.template_service = template_service
        self.mcp_manager = MCPServerManager(metrics=self.metrics,
                                            template_service=self.template_service)
        ...
        self.tabs = TabsPresenter(
            self.request_manager, self.state_manager, self.settings,
            metrics=self.metrics,
            history_manager=self.history_manager,
            template_service=self.template_service,
        )
```

---

### `pypost/core/mcp_server.py`

**Change:** Accept `template_service: TemplateService | None = None`, pass to `MCPServerImpl`.

```python
# add import
from pypost.core.template_service import TemplateService

class MCPServerManager(QObject):
    def __init__(self, metrics: MetricsManager | None = None,
                 template_service: TemplateService | None = None):
        ...
        self._impl = MCPServerImpl(metrics=metrics, template_service=template_service)
```

---

### `pypost/core/mcp_server_impl.py`

**Change:** Remove the `else` branch that creates a fallback `TemplateService()`. Set
`self._template_service` directly from the parameter (may be `None`).

```python
# Before:
if template_service is not None:
    self._template_service = template_service
    logger.debug(...)
else:
    self._template_service = TemplateService()
    logger.debug(...)

# After:
self._template_service = template_service
if template_service is not None:
    logger.debug("MCPServerImpl: using injected TemplateService id=%d", id(template_service))
```

Also update `RequestService` construction to pass the (potentially `None`) value through:
```python
self.request_service = RequestService(metrics=self._metrics,
                                      template_service=self._template_service)
```
(No change needed here — already passing `self._template_service`.)

---

### `pypost/core/worker.py`

**Change:** Accept `template_service: TemplateService | None = None`, store it, pass to
`RequestService`.

```python
# add import
from pypost.core.template_service import TemplateService

class RequestWorker(QThread):
    def __init__(
        self,
        request_data: RequestData,
        variables: dict = None,
        metrics: MetricsManager | None = None,
        history_manager: HistoryManager | None = None,
        collection_name: str | None = None,
        template_service: TemplateService | None = None,
    ):
        ...
        self.service = RequestService(metrics=metrics, history_manager=history_manager,
                                      template_service=template_service)
```

---

### `pypost/core/request_service.py`

**Change:** Remove the `else` branch that creates a fallback `TemplateService()`.

```python
# Before:
if template_service is not None:
    self._template_service = template_service
    logger.debug(...)
else:
    self._template_service = TemplateService()
    logger.debug(...)

# After:
self._template_service = template_service
if template_service is not None:
    logger.debug("RequestService: using injected TemplateService id=%d", id(template_service))
```

Note: `self._template_service` may be `None` in tests that do not inject it. All call sites
(`render_string`, `parse`) guard via the existing `if self._template_service:` or must be reviewed
to ensure `None` is safe. Since `_execute_mcp` and the history block both call
`self._template_service.render_string(...)` unconditionally, either:
- (a) callers must always inject a real instance (production path guaranteed by main.py), or
- (b) the methods must guard with `if self._template_service`.

**Decision:** Use option (a). Production always injects; tests that need rendering inject a stub.
Tests that do not call render paths can pass `None`. No defensive guarding added (keeps code
minimal, avoids hiding missing injection in production).

---

### `pypost/core/http_client.py`

**Change:** Remove the `else` branch that creates a fallback `TemplateService()`.

```python
# Before:
if template_service is not None:
    self._template_service = template_service
    logger.debug(...)
else:
    self._template_service = TemplateService()
    logger.debug(...)

# After:
self._template_service = template_service
if template_service is not None:
    logger.debug("HTTPClient: using injected TemplateService id=%d", id(template_service))
```

Same note as `RequestService`: production always injects; tests that exercise rendering must
inject a stub.

---

### `pypost/ui/presenters/tabs_presenter.py`

**Change:** Accept `template_service: TemplateService | None = None` in `TabsPresenter.__init__`,
store it as `self._template_service`, and pass it when constructing `RequestWorker` at line 316.

```python
# add import
from pypost.core.template_service import TemplateService

class TabsPresenter(QObject):
    def __init__(
        self,
        request_manager: RequestManager,
        state_manager: StateManager,
        settings: AppSettings,
        metrics: MetricsManager | None = None,
        history_manager: HistoryManager | None = None,
        template_service: TemplateService | None = None,
        parent: QObject | None = None,
    ) -> None:
        ...
        self._template_service = template_service

# At line 316 (RequestWorker construction):
worker = RequestWorker(
    request_data,
    variables=self._current_variables,
    metrics=self._metrics,
    history_manager=self._history_manager,
    collection_name=collection_name,
    template_service=self._template_service,
)
```

---

## Injection Chain Validation

After all changes, the full path from composition root to leaf:

| Hop | From | To | Parameter |
|-----|------|----|-----------|
| 1 | `main.py` | `MainWindow` | `template_service=template_service` |
| 2 | `MainWindow` | `MCPServerManager` | `template_service=self.template_service` |
| 3 | `MCPServerManager` | `MCPServerImpl` | `template_service=template_service` |
| 4 | `MCPServerImpl` | `RequestService` | `template_service=self._template_service` |
| 5 | `RequestService` | `HTTPClient` | `template_service=self._template_service` |
| 2b | `MainWindow` | `TabsPresenter` | `template_service=self.template_service` |
| 3b | `TabsPresenter` | `RequestWorker` | `template_service=self._template_service` |
| 4b | `RequestWorker` | `RequestService` | `template_service=template_service` |
| 5b | `RequestService` | `HTTPClient` | `template_service=self._template_service` |

---

## Acceptance Criteria Mapping

| AC | How satisfied |
|----|---------------|
| 1. Exactly one `TemplateService` instance | Created once in `main.py` |
| 2. No internal fallback construction | `else: TemplateService()` removed from 3 classes |
| 3. Full injection chain unbroken | See chain table above |
| 4. All existing tests pass | No logic changes; only parameter threading |
| 5. Unit tests can inject mock | All constructors accept `TemplateService \| None` |

---

## Testing Notes

- Tests that previously relied on the silent `TemplateService()` fallback will still pass because
  the `| None = None` default is preserved. Those tests simply do not call render paths.
- Tests that exercise template rendering should inject `TemplateService()` explicitly (or a stub).
- No new test files are required by this ticket.
