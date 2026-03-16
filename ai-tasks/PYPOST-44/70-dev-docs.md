# PYPOST-44: Developer Documentation

## What Changed

PYPOST-44 removes the `MetricsManager` singleton pattern and replaces it with constructor
injection. `MetricsManager` is now a plain service object constructed once in `main.py` and
passed down through every component that needs to track metrics.

---

## MetricsManager: Before and After

### Before

```python
# Any module could do this anywhere — global shared state:
MetricsManager().track_gui_send_click()
```

### After

```python
# Constructor receives the instance:
class RequestWidget:
    def __init__(self, request_data=None, metrics: MetricsManager | None = None):
        self._metrics = metrics

    def _on_send(self):
        if self._metrics:
            self._metrics.track_gui_send_click()
```

---

## Injection Chain

```
main.py
  metrics = MetricsManager()          # only instantiation in production code
  metrics.start_server(host, port)
  MainWindow(metrics=metrics)
    self.metrics = metrics
    ├── CollectionsPresenter(rm, sm, self.metrics, icons)
    ├── TabsPresenter(rm, sm, settings, metrics=self.metrics)
    │     self._metrics = metrics
    │     ├── [add_new_tab] RequestTab(data, metrics=self._metrics)
    │     │     ├── RequestWidget(data, metrics=metrics)
    │     │     └── ResponseView(metrics=metrics)
    │     └── [_handle_send_request] RequestWorker(data, vars, metrics=self._metrics)
    │           RequestService(metrics=metrics)
    │             HTTPClient(metrics=metrics)
    └── MCPServerManager(metrics=self.metrics)
          MCPServerImpl(metrics=metrics)
            RequestService(metrics=metrics)
```

---

## Constructor Signatures

| Class | New parameter |
|-------|---------------|
| `MainWindow` | `metrics: MetricsManager` (required) |
| `TabsPresenter` | `metrics: MetricsManager | None = None` |
| `RequestTab` | `metrics: MetricsManager | None = None` |
| `RequestWidget` | `metrics: MetricsManager | None = None` |
| `ResponseView` | `metrics: MetricsManager | None = None` |
| `HTTPClient` | `metrics: MetricsManager | None = None` |
| `RequestService` | `metrics: MetricsManager | None = None` |
| `RequestWorker` | `metrics: MetricsManager | None = None` |
| `MCPServerImpl` | `metrics: MetricsManager | None = None` |
| `MCPServerManager` | `metrics: MetricsManager | None = None` |

`MainWindow` receives the real instance. All other classes default to `None` so they can be
instantiated in tests without a running metrics server.

---

## None-Guard Pattern

Every tracking call site uses an inline guard:

```python
if self._metrics:
    self._metrics.track_xxx(...)
```

This is intentional. `metrics=None` is a valid state in tests. There is no NullObject class.

---

## Writing Tests

Inject a `MagicMock()` in place of the real `MetricsManager`:

```python
from unittest.mock import MagicMock
from pypost.core.http_client import HTTPClient

class TestHTTPClient(unittest.TestCase):
    def setUp(self):
        self.client = HTTPClient(metrics=MagicMock())
```

No `patch()` on module imports is required. The mock is passed directly.

To assert that a metric was tracked:

```python
mock_metrics = MagicMock()
client = HTTPClient(metrics=mock_metrics)
# ... run request ...
mock_metrics.track_request_sent.assert_called_once_with("GET")
```

To test with no metrics tracking (verify no crash):

```python
client = HTTPClient()  # metrics defaults to None — all track_* calls are skipped
```

---

## Adding a New Tracking Call

1. Add a `Counter` definition in `MetricsManager._init_metrics()` in
   `pypost/core/metrics.py`.
2. Add a `track_*` method to `MetricsManager`.
3. In the consumer class, call it with the None-guard:
   ```python
   if self._metrics:
       self._metrics.track_new_event(label_value)
   ```
4. `MetricsManager` is already injected; no import changes are needed in the consumer.

---

## Logging

The following modules emit structured log records:

| Module | Events logged |
|--------|--------------|
| `pypost/main.py` | `PyPost starting up`, `PyPost shutting down` |
| `pypost/core/metrics.py` | `Metrics server started on {host}:{port}`, `Metrics server stopped` |
| `pypost/core/http_client.py` | `Request failed: {method} {url} — {error}` (ERROR) |
| `pypost/core/worker.py` | `RequestWorker failed: {error}` with full traceback (ERROR) |
| `pypost/core/mcp_server.py` | `MCP server started on {host}:{port}`, `MCP server stopped` |
| `pypost/ui/main_window.py` | `main_window_initialized`, `settings_applied`, `metrics_server_restarting` |

All records use `logging.getLogger(__name__)`. The root logger is configured in `main.py` with
`basicConfig(level=logging.INFO)`.

---

## Files Modified

| File | Change |
|------|--------|
| `pypost/core/metrics.py` | Removed singleton machinery; added logging |
| `pypost/main.py` | Pass `metrics` to `MainWindow`; added logging setup |
| `pypost/ui/main_window.py` | Accept + store `metrics`; propagate to sub-components |
| `pypost/ui/presenters/tabs_presenter.py` | `TabsPresenter` + `RequestTab` accept `metrics` |
| `pypost/ui/widgets/request_editor.py` | `RequestWidget` accepts + uses `metrics` |
| `pypost/ui/widgets/response_view.py` | `ResponseView` accepts + uses `metrics` |
| `pypost/core/http_client.py` | Accepts + uses `metrics`; logs failures |
| `pypost/core/request_service.py` | Accepts + uses `metrics`; forwards to `HTTPClient` |
| `pypost/core/worker.py` | Accepts `metrics`; forwards to `RequestService`; logs errors |
| `pypost/core/mcp_server_impl.py` | Accepts + uses `metrics`; forwards to `RequestService` |
| `pypost/core/mcp_server.py` | Accepts `metrics`; forwards to `MCPServerImpl`; logs lifecycle |
| `tests/test_tabs_presenter.py` | Inject `MagicMock()` as `metrics` |
| `tests/test_http_client.py` | Replace patcher with injected `MagicMock()` |
| `tests/test_request_service.py` | Replace patchers with injected `MagicMock()` |

---

## Known Limitations

- No `IMetricsManager` protocol exists. Consumers depend on the concrete class. See TD-1 in
  `60-review.md` for the recommended follow-up.
- `MetricsManager` bundles Prometheus counters, server lifecycle, and MCP resource exposure.
  See TD-3 in `60-review.md` for the recommended future split.
