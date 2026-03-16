# PYPOST-44: Replace MetricsManager Singleton with Injection

## Jira Metadata

| Field      | Value                                      |
|------------|--------------------------------------------|
| Key        | PYPOST-44                                  |
| Type       | Debt                                       |
| Priority   | High (P1)                                  |
| Status     | To Do                                      |
| Labels     | PYPOST-40, refactoring                     |
| Origin     | PYPOST-40 audit, recommendation R2         |

---

## Problem Statement

`MetricsManager` is a thread-safe singleton accessed throughout the codebase via direct
instantiation (`MetricsManager()`). This creates hidden global-state dependencies in UI
presenters, widgets, and core services, violating the Dependency Inversion Principle (DIP) and
making unit testing extremely difficult (tests cannot swap in a fake or null implementation).

The audit report (PYPOST-40) listed this as a **P1 tech debt** item, noting that `MetricsManager`
is called in at least nine different modules.

---

## Goals

1. Remove the singleton pattern (`__new__`/`_instance`/`_lock`) from `MetricsManager`.
2. Construct a single `MetricsManager` instance in `main.py` and pass it through constructors
   down to every consumer.
3. All consumers must receive `MetricsManager` as a constructor argument — no module-level
   `MetricsManager()` calls outside of `main.py`.
4. All existing unit tests must continue to pass.
5. A lightweight `FakeMetricsManager` (or use of `unittest.mock`) must be usable in tests
   without starting a real server.

---

## Scope of Change

### Files that currently call `MetricsManager()` directly

| Module | Usage |
|--------|-------|
| `pypost/main.py` | Creates instance, calls `start_server` / `stop_server` — **already correct entry point** |
| `pypost/ui/main_window.py` | Passes `MetricsManager()` to `CollectionsPresenter`; calls `restart_server` |
| `pypost/ui/presenters/tabs_presenter.py` | Calls multiple `track_*` methods inline |
| `pypost/ui/presenters/collections_presenter.py` | Already accepts `metrics: MetricsManager` in constructor — **already injected** |
| `pypost/ui/widgets/request_editor.py` | Calls `track_gui_send_click`, `track_gui_save_action`, etc. |
| `pypost/ui/widgets/response_view.py` | Calls `track_gui_response_search_action` |
| `pypost/core/http_client.py` | Calls `track_request_sent`, `track_response_received` |
| `pypost/core/request_service.py` | Calls `track_request_sent`, `track_response_received` |
| `pypost/core/mcp_server_impl.py` | Calls `track_mcp_request_received`, `track_mcp_response_sent` |

### Injection chain (constructor propagation)

```
main.py
  └── metrics = MetricsManager()
        ├── MainWindow(metrics)
        │     ├── CollectionsPresenter(request_manager, state_manager, metrics, icons)
        │     │     [already injected — no change needed]
        │     ├── TabsPresenter(request_manager, state_manager, settings, metrics)
        │     │     └── RequestTab(request_data, metrics)
        │     │           ├── RequestWidget(request_data, metrics)
        │     │           └── ResponseView(metrics)
        │     └── MainWindow stores self.metrics, calls self.metrics.restart_server(...)
        ├── HTTPClient(metrics)
        │     [used inside RequestService]
        ├── RequestService(metrics)
        │     [used inside MCPServerImpl and TabsPresenter worker]
        └── MCPServerImpl(name, metrics)
```

---

## Functional Requirements

### FR-1: Remove singleton pattern from MetricsManager
- Delete `__new__`, `_instance`, and `_lock` class attributes.
- `MetricsManager.__init__` must be idempotent-free (no `_initialized` guard needed).
- The class becomes a plain service object.

### FR-2: Construct MetricsManager once in main.py
- `main.py` already creates `metrics_manager = MetricsManager()` — this remains as-is.
- `metrics_manager` is passed into `MainWindow(metrics=metrics_manager)`.

### FR-3: MainWindow accepts MetricsManager via constructor
- Signature change: `MainWindow.__init__(self, metrics: MetricsManager) -> None`.
- Store as `self.metrics`.
- Pass `self.metrics` to `CollectionsPresenter` (already done), `TabsPresenter`, and any
  direct calls like `restart_server`.
- Remove the inline `MetricsManager()` call for `restart_server`.

### FR-4: TabsPresenter accepts MetricsManager via constructor
- Add `metrics: MetricsManager` parameter to `TabsPresenter.__init__`.
- Store as `self._metrics`.
- Replace all inline `MetricsManager()` calls with `self._metrics`.

### FR-5: RequestTab accepts MetricsManager via constructor
- Add `metrics: MetricsManager` parameter to `RequestTab.__init__`.
- Forward to `RequestWidget` and `ResponseView` constructors.

### FR-6: RequestWidget accepts MetricsManager via constructor
- Add `metrics: MetricsManager` parameter to `RequestWidget.__init__`.
- Store as `self._metrics`.
- Replace all inline `MetricsManager()` calls with `self._metrics`.

### FR-7: ResponseView accepts MetricsManager via constructor
- Add `metrics: MetricsManager` parameter to `ResponseView.__init__`.
- Store as `self._metrics`.
- Replace all inline `MetricsManager()` calls with `self._metrics`.

### FR-8: HTTPClient accepts MetricsManager via constructor
- Add `metrics: MetricsManager` parameter to `HTTPClient.__init__`.
- Store as `self._metrics`.
- Replace all inline `MetricsManager()` calls with `self._metrics`.

### FR-9: RequestService accepts MetricsManager via constructor
- Add `metrics: MetricsManager` parameter to `RequestService.__init__`.
- Store as `self._metrics`.
- Pass `self._metrics` to `HTTPClient(metrics=self._metrics)` instantiated internally,
  OR accept an `HTTPClient` instance — follow existing architecture.
- Replace all inline `MetricsManager()` calls with `self._metrics`.

### FR-10: MCPServerImpl accepts MetricsManager via constructor
- Add `metrics: MetricsManager` parameter to `MCPServerImpl.__init__`.
- Store as `self._metrics`.
- Replace all inline `MetricsManager()` calls with `self._metrics`.

### FR-11: No MetricsManager() calls outside main.py
- After the refactor, the only `MetricsManager()` instantiation in production code is in
  `main.py`.
- All other modules receive the instance via constructors.

---

## Non-Functional Requirements

### NFR-1: Testability
- Tests must be able to inject a `MagicMock()` or `FakeMetricsManager` in place of the real
  instance.
- No test should require a running Prometheus/uvicorn server.

### NFR-2: No behaviour change
- The application must behave identically at runtime; no metrics must be lost.
- Server lifecycle (`start_server`, `stop_server`, `restart_server`) is unchanged.

### NFR-3: Code style
- Line length ≤ 100 characters.
- UTF-8, LF endings, no trailing whitespace.
- All code and comments in English.

---

## Out of Scope

- Introducing an abstract `IMetricsManager` protocol/interface (may be addressed separately).
- Changing metric names, labels, or Prometheus counter definitions.
- Refactoring `MCPServerImpl` internals beyond injecting metrics.
- Any changes to test infrastructure beyond making existing tests compatible.

---

## Acceptance Criteria

- [ ] `MetricsManager` has no singleton machinery.
- [ ] `main.py` constructs one instance and passes it to `MainWindow`.
- [ ] `MainWindow`, `TabsPresenter`, `RequestTab`, `RequestWidget`, `ResponseView`,
      `HTTPClient`, `RequestService`, and `MCPServerImpl` all receive `MetricsManager`
      via constructor.
- [ ] No production module outside `main.py` calls `MetricsManager()`.
- [ ] `make test` (or equivalent) passes with no regressions.
- [ ] Existing tests that instantiate affected classes use a mock/fake for `metrics`.
