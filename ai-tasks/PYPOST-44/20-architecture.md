# PYPOST-44: Architecture — Replace MetricsManager Singleton with Injection

## 1. Overview

This document describes the design for removing the `MetricsManager` singleton pattern and
replacing it with constructor injection throughout the application. The single `MetricsManager`
instance is created in `main.py` and propagated down the full object graph.

---

## 2. Current State Analysis

### 2.1 Singleton machinery (to be removed)

`pypost/core/metrics.py` currently uses a double-checked locking singleton:

```python
class MetricsManager:
    _instance = None          # class attr
    _lock = threading.Lock()  # class attr

    def __new__(cls):         # intercepts every MetricsManager() call
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:   # guard against re-init
            return
        self._initialized = True
        ...
```

### 2.2 Direct call sites (`MetricsManager()` outside `main.py`)

| File | Call site (approx. line) | Method called |
|------|--------------------------|---------------|
| `pypost/ui/main_window.py` | 40 | passed to `CollectionsPresenter` |
| `pypost/ui/main_window.py` | 163 | `restart_server` |
| `pypost/ui/presenters/tabs_presenter.py` | 204 | `track_gui_new_tab_action` |
| `pypost/ui/presenters/tabs_presenter.py` | 293 | `track_request_sent` |
| `pypost/ui/presenters/tabs_presenter.py` | 320 | `track_response_received` |
| `pypost/ui/presenters/tabs_presenter.py` | 402 | `track_gui_save_action` |
| `pypost/ui/presenters/tabs_presenter.py` | 435 | `track_gui_save_action` |
| `pypost/ui/widgets/request_editor.py` | 128 | `track_gui_method_body_autoswitch` |
| `pypost/ui/widgets/request_editor.py` | 165 | `track_gui_send_click` |
| `pypost/ui/widgets/request_editor.py` | 172 | `track_gui_save_action` |
| `pypost/ui/widgets/request_editor.py` | 194 | `track_gui_save_as_action` |
| `pypost/ui/widgets/response_view.py` | 105 | `track_gui_response_search_action` |
| `pypost/ui/widgets/response_view.py` | 120 | `track_gui_response_search_action` |
| `pypost/ui/widgets/response_view.py` | 191 | `track_gui_response_search_action` |
| `pypost/core/http_client.py` | 138 | `track_request_sent` |
| `pypost/core/http_client.py` | 190 | `track_response_received` |
| `pypost/core/request_service.py` | 50 | `track_request_sent` |
| `pypost/core/request_service.py` | 52 | `track_response_received` |
| `pypost/core/mcp_server_impl.py` | 44 | `track_mcp_request_received` |
| `pypost/core/mcp_server_impl.py` | 65 | `track_mcp_response_sent` |
| `pypost/core/mcp_server_impl.py` | 72 | `track_mcp_response_sent` |

### 2.3 Already-injected consumer

`CollectionsPresenter` already accepts `metrics: MetricsManager` in its constructor and stores it
as `self._metrics`. It is a reference implementation — no change needed.

---

## 3. Target Injection Graph

```
main.py
  metrics = MetricsManager()           # only instantiation in production code
  metrics.start_server(host, port)
  MainWindow(metrics=metrics)
    self.metrics = metrics
    ├── CollectionsPresenter(rm, sm, self.metrics, icons)  # unchanged
    ├── TabsPresenter(rm, sm, settings, metrics=self.metrics)
    │     self._metrics = metrics
    │     ├── [add_new_tab] RequestTab(request_data, metrics=self._metrics)
    │     │     ├── RequestWidget(request_data, metrics=metrics)
    │     │     │     self._metrics = metrics
    │     │     └── ResponseView(metrics=metrics)
    │     │           self._metrics = metrics
    │     └── [_handle_send_request] RequestWorker(rd, vars, metrics=self._metrics)
    │           self.service = RequestService(metrics=metrics)
    │                 self._metrics = metrics
    │                 self.http_client = HTTPClient(metrics=self._metrics)
    │                       self._metrics = metrics
    └── MCPServerManager(metrics=self.metrics)
          self._impl = MCPServerImpl(metrics=metrics)
                self._metrics = metrics
                self.request_service = RequestService(metrics=self._metrics)
```

---

## 4. File-by-File Change Specification

### 4.1 `pypost/core/metrics.py`

**Goal:** Remove singleton machinery; `MetricsManager` becomes a plain service class.

Changes:
- Delete class attributes `_instance` and `_lock`.
- Delete `__new__` entirely.
- Delete the `if self._initialized: return` / `self._initialized = True` guard in `__init__`.
- All other code (counter definitions, server lifecycle, tracking methods) is unchanged.

```python
# BEFORE
class MetricsManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        ...

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        ...

# AFTER
class MetricsManager:
    def __init__(self):
        self.registry = CollectorRegistry()
        ...
```

Remove `import threading` only if no other code in the file uses it. (It is also used by
`self.server_lock = threading.Lock()` inside `__init__`, so the import stays.)

---

### 4.2 `pypost/main.py`

**Goal:** Pass `metrics_manager` to `MainWindow`.

```python
# BEFORE
window = MainWindow()

# AFTER
window = MainWindow(metrics=metrics_manager)
```

No other changes.

---

### 4.3 `pypost/ui/main_window.py`

**Goal:** Accept and store `metrics`; propagate to all sub-components; remove inline calls.

Constructor signature:

```python
# BEFORE
def __init__(self) -> None:

# AFTER
def __init__(self, metrics: MetricsManager) -> None:
```

Changes inside `__init__`:

```python
# Add near the top of __init__, before other assignments:
self.metrics = metrics

# BEFORE
self.collections = CollectionsPresenter(
    self.request_manager, self.state_manager, MetricsManager(), self.icons,
)
self.tabs = TabsPresenter(self.request_manager, self.state_manager, self.settings)
self.mcp_manager = MCPServerManager()

# AFTER
self.collections = CollectionsPresenter(
    self.request_manager, self.state_manager, self.metrics, self.icons,
)
self.tabs = TabsPresenter(
    self.request_manager, self.state_manager, self.settings, metrics=self.metrics
)
self.mcp_manager = MCPServerManager(metrics=self.metrics)
```

Change inside `open_settings`:

```python
# BEFORE
MetricsManager().restart_server(self.settings.metrics_host, self.settings.metrics_port)

# AFTER
self.metrics.restart_server(self.settings.metrics_host, self.settings.metrics_port)
```

Remove the `from pypost.core.metrics import MetricsManager` import (no longer needed after the
call in `open_settings` is replaced and `CollectionsPresenter` receives `self.metrics`). If the
type annotation `MetricsManager` is kept for the constructor parameter, keep the import.

---

### 4.4 `pypost/ui/presenters/tabs_presenter.py`

**Goal:** Add `metrics` to `TabsPresenter` and `RequestTab`; forward to widgets and worker.

#### 4.4.1 `TabsPresenter`

```python
# BEFORE
def __init__(
    self,
    request_manager: RequestManager,
    state_manager: StateManager,
    settings: AppSettings,
    parent: QObject | None = None,
) -> None:
    ...

# AFTER
def __init__(
    self,
    request_manager: RequestManager,
    state_manager: StateManager,
    settings: AppSettings,
    metrics: MetricsManager | None = None,
    parent: QObject | None = None,
) -> None:
    ...
    self._metrics = metrics
```

Replace every `MetricsManager()` call with `self._metrics` guarded by a None check:

```python
# Pattern for all call sites:
if self._metrics:
    self._metrics.track_xxx(...)
```

In `add_new_tab`:

```python
# BEFORE
tab = RequestTab(request_data)

# AFTER
tab = RequestTab(request_data, metrics=self._metrics)
```

In `_handle_send_request`:

```python
# BEFORE
worker = RequestWorker(request_data, variables=self._current_variables)

# AFTER
worker = RequestWorker(request_data, variables=self._current_variables, metrics=self._metrics)
```

#### 4.4.2 `RequestTab`

```python
# BEFORE
def __init__(self, request_data: RequestData | None = None) -> None:
    ...
    self.request_editor = RequestWidget(request_data)
    self.response_view = ResponseView()

# AFTER
def __init__(
    self,
    request_data: RequestData | None = None,
    metrics: MetricsManager | None = None,
) -> None:
    ...
    self.request_editor = RequestWidget(request_data, metrics=metrics)
    self.response_view = ResponseView(metrics=metrics)
```

---

### 4.5 `pypost/ui/widgets/request_editor.py` (`RequestWidget`)

```python
# BEFORE
def __init__(self, request_data: RequestData = None):
    ...

# AFTER
def __init__(self, request_data: RequestData = None, metrics: MetricsManager | None = None):
    ...
    self._metrics = metrics
```

Replace every `MetricsManager()` call:

```python
# BEFORE
MetricsManager().track_gui_method_body_autoswitch(method)

# AFTER
if self._metrics:
    self._metrics.track_gui_method_body_autoswitch(method)
```

Apply the same None-guard pattern to all four call sites (lines ~128, ~165, ~172, ~194).

---

### 4.6 `pypost/ui/widgets/response_view.py` (`ResponseView`)

```python
# BEFORE
def __init__(self, indent_size=2):
    ...

# AFTER
def __init__(self, indent_size=2, metrics: MetricsManager | None = None):
    ...
    self._metrics = metrics
```

Replace every `MetricsManager()` call with guarded `self._metrics` (three call sites, ~lines
105, 120, 191).

---

### 4.7 `pypost/core/http_client.py` (`HTTPClient`)

```python
# BEFORE
def __init__(self):
    self.session = requests.Session()

# AFTER
def __init__(self, metrics: MetricsManager | None = None):
    self.session = requests.Session()
    self._metrics = metrics
```

Replace two `MetricsManager()` calls with guarded `self._metrics` (~lines 138, 190).

---

### 4.8 `pypost/core/request_service.py` (`RequestService`)

```python
# BEFORE
def __init__(self):
    self.http_client = HTTPClient()
    self.mcp_client = MCPClientService()

# AFTER
def __init__(self, metrics: MetricsManager | None = None):
    self._metrics = metrics
    self.http_client = HTTPClient(metrics=self._metrics)
    self.mcp_client = MCPClientService()
```

Replace two `MetricsManager()` calls in `_execute_mcp` with guarded `self._metrics` (~lines 50,
52-53).

---

### 4.9 `pypost/core/worker.py` (`RequestWorker`)

```python
# BEFORE
def __init__(self, request_data: RequestData, variables: dict = None):
    ...
    self.service = RequestService()

# AFTER
def __init__(
    self,
    request_data: RequestData,
    variables: dict = None,
    metrics: MetricsManager | None = None,
):
    ...
    self.service = RequestService(metrics=metrics)
```

No direct `MetricsManager()` calls in this file — only the constructor propagation matters.

---

### 4.10 `pypost/core/mcp_server_impl.py` (`MCPServerImpl`)

```python
# BEFORE
def __init__(self, name: str = "pypost-server"):
    ...
    self.request_service = RequestService()

# AFTER
def __init__(self, name: str = "pypost-server", metrics: MetricsManager | None = None):
    ...
    self._metrics = metrics
    self.request_service = RequestService(metrics=self._metrics)
```

Replace three `MetricsManager()` calls with guarded `self._metrics` (~lines 44, 65-66, 72-73).

---

### 4.11 `pypost/core/mcp_server.py` (`MCPServerManager`)

```python
# BEFORE
def __init__(self):
    ...
    self._impl = MCPServerImpl()

# AFTER
def __init__(self, metrics: MetricsManager | None = None):
    ...
    self._impl = MCPServerImpl(metrics=metrics)
```

No direct `MetricsManager()` calls in this file — only the constructor propagation matters.

---

## 5. Test Changes

### 5.1 `tests/test_tabs_presenter.py`

`TabsPresenter` now requires or accepts a `metrics` parameter.

```python
# BEFORE (in _make_presenter and inline)
return TabsPresenter(rm, sm, settings)
...
p = TabsPresenter(rm, sm, AppSettings())

# AFTER
return TabsPresenter(rm, sm, settings, metrics=MagicMock())
...
p = TabsPresenter(rm, sm, AppSettings(), metrics=MagicMock())
```

Import `MagicMock` is already present in this file.

### 5.2 `tests/test_http_client.py`

The `metrics_patcher` workaround is no longer needed. Inject a mock directly:

```python
# BEFORE
def setUp(self):
    self.metrics_patcher = patch("pypost.core.http_client.MetricsManager")
    self.metrics_patcher.start()
    self.client = HTTPClient()

def tearDown(self):
    self.metrics_patcher.stop()

# AFTER
def setUp(self):
    self.client = HTTPClient(metrics=MagicMock())
```

Remove unused `patch` import if nothing else in the file uses it.

### 5.3 `tests/test_request_service.py`

Same pattern — remove patchers, inject mock directly in all three test classes:

```python
# BEFORE
def setUp(self):
    self.metrics_patcher = patch("pypost.core.request_service.MetricsManager")
    self.metrics_patcher.start()
    self.svc = RequestService()

def tearDown(self):
    self.metrics_patcher.stop()

# AFTER
def setUp(self):
    self.svc = RequestService(metrics=MagicMock())
```

Apply to `TestRequestServiceExecuteHTTP`, `TestRequestServicePostScript`, and
`TestRequestServiceMCP`.

### 5.4 `tests/test_request_editor_method_tab_switch.py`

No changes required. `RequestWidget()` is called without arguments; `metrics` defaults to `None`
and all tracking calls are None-guarded, so no crash occurs.

### 5.5 Other test files

`test_collections_presenter.py` — uses `FakeMetrics`; `CollectionsPresenter` already injects
correctly. No changes needed.

All other test files do not instantiate affected classes. No changes needed.

---

## 6. None-Guard Pattern

For all optional `metrics` parameters, use an inline guard at each call site:

```python
if self._metrics:
    self._metrics.track_xxx(...)
```

This is preferred over a NullObject pattern because:
- It keeps the change minimal and explicit.
- The `None` case only occurs in tests that opt out of metric tracking.
- No new classes or protocols are introduced (out of scope per requirements).

---

## 7. Import Cleanup

After removing inline `MetricsManager()` calls, the import
`from pypost.core.metrics import MetricsManager` remains in each file that uses `MetricsManager`
as a type annotation for the constructor parameter. Files that no longer reference `MetricsManager`
by name at all may drop the import. The Junior Engineer should verify each file case by case.

---

## 8. Files Changed Summary

| File | Change type |
|------|-------------|
| `pypost/core/metrics.py` | Remove singleton machinery |
| `pypost/main.py` | Pass `metrics` to `MainWindow` |
| `pypost/ui/main_window.py` | Accept + store `metrics`; propagate |
| `pypost/ui/presenters/tabs_presenter.py` | Accept `metrics` in `TabsPresenter` + `RequestTab`; forward |
| `pypost/ui/widgets/request_editor.py` | Accept + use `metrics` |
| `pypost/ui/widgets/response_view.py` | Accept + use `metrics` |
| `pypost/core/http_client.py` | Accept + use `metrics` |
| `pypost/core/request_service.py` | Accept + use `metrics`; forward to `HTTPClient` |
| `pypost/core/worker.py` | Accept `metrics`; forward to `RequestService` |
| `pypost/core/mcp_server_impl.py` | Accept + use `metrics`; forward to `RequestService` |
| `pypost/core/mcp_server.py` | Accept `metrics`; forward to `MCPServerImpl` |
| `tests/test_tabs_presenter.py` | Add `MagicMock()` as `metrics` arg |
| `tests/test_http_client.py` | Replace patcher with injected `MagicMock()` |
| `tests/test_request_service.py` | Replace patchers with injected `MagicMock()` |

---

## 9. Acceptance Criteria Mapping

| AC | Design element |
|----|----------------|
| `MetricsManager` has no singleton machinery | §4.1 |
| `main.py` constructs one instance | §4.2 |
| All consumers receive via constructor | §4.3 – §4.11 |
| No production module outside `main.py` calls `MetricsManager()` | §4.1 – §4.11 |
| `make test` passes | §5 |
| Existing tests use mock/fake for `metrics` | §5 |
