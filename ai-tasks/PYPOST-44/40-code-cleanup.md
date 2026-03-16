# PYPOST-44: Code Cleanup

## Summary

Implementation of `MetricsManager` singleton removal and constructor injection is complete.
All 103 tests pass (`make test`).

---

## Changes Made

### `pypost/core/metrics.py`
- Removed `_instance` class attribute, `_lock` class attribute, `__new__` method, and
  `_initialized` guard from `__init__`. `MetricsManager` is now a plain service class.
- `import threading` retained (used by `self.server_lock = threading.Lock()` in `__init__`).

### `pypost/main.py`
- `MainWindow()` → `MainWindow(metrics=metrics_manager)`.

### `pypost/ui/main_window.py`
- Constructor signature: `def __init__(self, metrics: MetricsManager) -> None`.
- `self.metrics = metrics` stored near the top of `__init__`.
- `MetricsManager()` call in `CollectionsPresenter(...)` replaced with `self.metrics`.
- `TabsPresenter(...)` now receives `metrics=self.metrics`.
- `MCPServerManager()` → `MCPServerManager(metrics=self.metrics)`.
- `MetricsManager().restart_server(...)` in `open_settings` → `self.metrics.restart_server(...)`.

### `pypost/ui/presenters/tabs_presenter.py`
- `RequestTab.__init__` accepts `metrics: MetricsManager | None = None`; forwards to
  `RequestWidget` and `ResponseView`.
- `TabsPresenter.__init__` accepts `metrics: MetricsManager | None = None`; stores as
  `self._metrics`.
- All four `MetricsManager()` call sites replaced with `if self._metrics:` guarded calls.
- `RequestTab(request_data)` → `RequestTab(request_data, metrics=self._metrics)`.
- `RequestWorker(...)` → `RequestWorker(..., metrics=self._metrics)`.

### `pypost/ui/widgets/request_editor.py`
- `RequestWidget.__init__` accepts `metrics: MetricsManager | None = None`; stored as
  `self._metrics`.
- Four `MetricsManager()` call sites replaced with `if self._metrics:` guarded calls.

### `pypost/ui/widgets/response_view.py`
- `ResponseView.__init__` accepts `metrics: MetricsManager | None = None`; stored as
  `self._metrics`.
- Three `MetricsManager()` call sites replaced with `if self._metrics:` guarded calls.

### `pypost/core/http_client.py`
- `HTTPClient.__init__` accepts `metrics: MetricsManager | None = None`; stored as
  `self._metrics`.
- Two `MetricsManager()` call sites replaced with `if self._metrics:` guarded calls.

### `pypost/core/request_service.py`
- `RequestService.__init__` accepts `metrics: MetricsManager | None = None`; stored as
  `self._metrics`; forwarded to `HTTPClient(metrics=self._metrics)`.
- Two `MetricsManager()` call sites in `_execute_mcp` replaced with `if self._metrics:`
  guarded calls.

### `pypost/core/worker.py`
- Added `from pypost.core.metrics import MetricsManager` import.
- `RequestWorker.__init__` accepts `metrics: MetricsManager | None = None`; forwarded to
  `RequestService(metrics=metrics)`.

### `pypost/core/mcp_server_impl.py`
- `MCPServerImpl.__init__` accepts `metrics: MetricsManager | None = None`; stored as
  `self._metrics`; forwarded to `RequestService(metrics=self._metrics)`.
- Three `MetricsManager()` call sites replaced with `if self._metrics:` guarded calls.

### `pypost/core/mcp_server.py`
- Added `from pypost.core.metrics import MetricsManager` import.
- `MCPServerManager.__init__` accepts `metrics: MetricsManager | None = None`; forwarded to
  `MCPServerImpl(metrics=metrics)`.

### `tests/test_tabs_presenter.py`
- `_make_presenter` now passes `metrics=MagicMock()` to `TabsPresenter`.
- Inline `TabsPresenter(rm, sm, AppSettings())` in `test_request_saved_signal_emitted` also
  updated to `TabsPresenter(rm, sm, AppSettings(), metrics=MagicMock())`.

### `tests/test_http_client.py`
- Removed `metrics_patcher` + `tearDown`. `HTTPClient` now instantiated as
  `HTTPClient(metrics=MagicMock())`.
- Removed unused `patch` import.

### `tests/test_request_service.py`
- Removed `metrics_patcher` + `tearDown` from all three test classes. `RequestService` now
  instantiated as `RequestService(metrics=MagicMock())` in each `setUp`.
- `patch` import retained (still used by `TestRequestServicePostScript` for `ScriptExecutor`).

---

## None-Guard Pattern Consistency

Every optional `metrics` parameter follows the same pattern at each call site:

```python
if self._metrics:
    self._metrics.track_xxx(...)
```

No NullObject or adapter introduced — consistent with the architecture decision (§6).

---

## Import Cleanup

- `from pypost.core.metrics import MetricsManager` kept in all files that use `MetricsManager`
  as a type annotation in the constructor parameter.
- No dangling imports introduced or left behind.

---

## Test Result

```
103 passed in 2.97s
```
