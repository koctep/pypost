# Unit Testability Patterns (PYPOST-382)

## Overview

The PYPOST-40 audit flagged `RequestService`, `HTTPClient`, and `MainWindow` as hard to unit
test because dependencies were created internally. PYPOST-382 adds **constructor injection
seams** where practical and documents established mocking patterns. Metrics consumers now
depend on `MetricsTrackerProtocol` ([PYPOST-73](https://pypost.atlassian.net/browse/PYPOST-73));
HTTP transport consumers depend on `HTTPClientProtocol`
([PYPOST-46](https://pypost.atlassian.net/browse/PYPOST-46)); request execution consumers
depend on `ExecuteRequestProtocol`
([PYPOST-51](https://pypost.atlassian.net/browse/PYPOST-51)); persistence consumers depend on
`StorageInterface` ([PYPOST-50](https://pypost.atlassian.net/browse/PYPOST-50)); collection
item dispatch uses a strategy registry
([PYPOST-48](https://pypost.atlassian.net/browse/PYPOST-48)).

## Composition root

`main.py` creates shared services once and passes them into `MainWindow`:

| Service | Created in | Injected into |
| --- | --- | --- |
| `ConfigManager` | `main.py` (before other services) | `MainWindow` → `StateManager` |
| `AppSettings` | `config_manager.load_config()` in `main.py` | `MetricsManager.start_server`, `AlertManager`, shared in UI |
| `MetricsManager` (facade) | `main.py` | `MainWindow`, presenters, workers |
| `MetricsTrackerProtocol` | type hint at consumers | `MagicMock(spec=MetricsTrackerProtocol)` in tests |
| `MetricsRegistry` (counters) | inside `MetricsManager` | use directly in counter-only unit tests |
| `MetricsServer` (uvicorn/MCP) | inside `MetricsManager` | started via `metrics.start_server()` in `main.py` |
| `TemplateService` | `main.py` | `MainWindow`, `MCPServerManager`, `TabsPresenter` → workers |
| `AlertManager` | `main.py` (from `AppSettings`) | `MainWindow` |

See [PYPOST-378 dev notes](../../ai-tasks/PYPOST-378/70-dev-docs.md) for the full
`TemplateService` chain and [template_service.md](template_service.md) for lifecycle design
(PYPOST-143).

## ConfigManager lifecycle

`main.py` is the composition root for settings: it constructs one `ConfigManager`, calls
`load_config()` once, and passes the same instance to `MainWindow`. Startup services that need
`AppSettings` before the UI exists (`MetricsManager.start_server`, `AlertManager`) read from that
single load — they are not a reason to defer or duplicate `ConfigManager` creation.

| Layer | Injection | Test substitute |
| --- | --- | --- |
| `MainWindow` | Optional `config_manager` (required in production from `main.py`) | `FakeConfigManager` or patched constructor |
| `StateManager` | Required `ConfigManager` | In-memory / temp-dir `ConfigManager` |

Production must inject from `main.py` so `settings.json` is read exactly once and
`StateManager` shares the same in-memory `AppSettings` object. See
[PYPOST-404 dev notes](../../ai-tasks/PYPOST-404/70-dev-docs.md) and
[architecture.md](architecture.md#composition-root-mainpy).

## Qt integration layer

PySide6-dependent modules live in `pypost/core/qt/` ([PYPOST-693](https://pypost.atlassian.net/browse/PYPOST-693)).
They use `QThread`, `QObject`, `Signal`, and `QTimer` to bridge async work to UI presenters.

| Module | Role |
| --- | --- |
| `qt/worker.py` | HTTP request execution off UI thread |
| `qt/mcp_server.py` | MCP uvicorn lifecycle + Qt signals |
| `qt/state_manager.py` | Debounced UI session persistence |
| `qt/metrics.py` | Metrics facade with Qt signals |
| `qt/collection_storage_*` | Async collection load queue |
| `qt/environment_storage_*` | Async env save/load with coalescing |
| `qt/encryption_migration_worker.py` | Background bulk re-encryption |

**Import rule:** headless or Qt-free code must not import from `pypost.core.qt`. Use
`pypost.core.metrics_protocol`, `pypost.core.mcp_server_impl`, and other Qt-free modules
instead.

**Test setup:** modules under `core/qt/` require `pytest-qt` or an offscreen `QApplication`.
Logger names use the `pypost.core.qt.*` prefix (e.g. `pypost.core.qt.worker`).

## TemplateService lifecycle

The module-level `template_service` global was removed in PYPOST-45. Production uses a **composition-
root singleton**: one `TemplateService(metrics=...)` in `main.py`, propagated by constructors.

| Layer | Injection | Test substitute |
| --- | --- | --- |
| `HTTPClient`, `RequestService`, `MCPServerImpl` | Optional `template_service` param | `TemplateService()` or `MagicMock()` |
| `MainWindow` | Required `template_service` | `MagicMock()` in patched constructor tests |
| Hover (`mixins.py`) | `VariableHoverResolver.set_template_service` from `MainWindow` / `RequestWidget` | Assign `VariableHoverHelper._template_service` |

Leaf classes may create a local `TemplateService()` when the parameter is omitted — intentional for
isolated unit tests. Production always injects from `main.py`.

**Coverage:** `TestHTTPClientInjection`, `TestRequestServiceInjection`,
`test_variable_hover.py` (hover property patching).

## MetricsTrackerProtocol and NullMetrics

Tracking consumers accept `MetricsTrackerProtocol | None` and normalize with
`resolve_metrics()` to `NULL_METRICS` when omitted ([PYPOST-74](https://pypost.atlassian.net/browse/PYPOST-74)).
Call sites invoke `self._metrics.track_*()` directly — no `if self._metrics` guards.

```python
from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics

class RequestService:
    def __init__(self, metrics: MetricsTrackerProtocol | None = None):
        self._metrics = resolve_metrics(metrics)
```

```python
from unittest.mock import MagicMock

from pypost.core.metrics_protocol import MetricsTrackerProtocol

metrics = MagicMock(spec=MetricsTrackerProtocol)
```

See [PYPOST-73](../../ai-tasks/PYPOST-73/70-dev-docs.md) and
[PYPOST-74](../../ai-tasks/PYPOST-74/70-dev-docs.md) dev notes.

### OpenTelemetry adapter (PYPOST-579)

Production can inject `OtelMetricsTracker` instead of Prometheus counters without changing
consumer call sites. Configure exporters on a `MeterProvider`, then:

```python
from opentelemetry.sdk.metrics import MeterProvider

from pypost.core.metrics_otel import create_otel_metrics_tracker

metrics = create_otel_metrics_tracker(meter_provider=provider)
```

Metric names and labels mirror `MetricsRegistry`. The desktop app default remains
`MetricsManager` (embedded Prometheus scrape). See `pypost/core/metrics_otel.py`.

## RequestService

### Injectable dependencies

| Parameter | Default when omitted | Test use |
| --- | --- | --- |
| `metrics` | `NULL_METRICS` (no-op) | `MagicMock(spec=MetricsTrackerProtocol)`; assert `track_*` calls |
| `template_service` | `None` | `TemplateService()` for render paths |
| `history_manager` | `None` | `MagicMock(spec=HistoryManager)` |
| `alert_manager` | `None` | `MagicMock(spec=AlertManager)` |
| `http_client` | new `HTTPClient(...)` | `MagicMock(spec=HTTPClientProtocol)` — avoids network I/O |
| `mcp_client` | new `MCPClientService()` | `MagicMock()` — avoids MCP transport |

### Recommended pattern

Prefer constructor injection over post-construction attribute replacement:

```python
from unittest.mock import MagicMock

from pypost.core.request_service import RequestService
from pypost.core.template_service import TemplateService

from pypost.core.http_client_protocol import HTTPClientProtocol

mock_http = MagicMock(spec=HTTPClientProtocol)
svc = RequestService(
    metrics=MagicMock(),
    template_service=TemplateService(),
    http_client=mock_http,
    mcp_client=MagicMock(),
)
mock_http.send_request.return_value = ...  # HTTPRequestResult stub
result = svc.execute(request_data)
```

Existing tests may still assign `svc.http_client = MagicMock()` after construction; both
approaches work. Constructor injection is preferred for new tests.

### Coverage

| Module | Class | Focus |
| --- | --- | --- |
| `tests/test_request_service.py` | `TestRequestServiceExecuteHTTP` | HTTP path with mocked client |
| `tests/test_request_service.py` | `TestRequestServiceInjection` | TemplateService, HTTP, MCP seams |
| `tests/test_request_service.py` | `TestRequestServiceMCP` | MCP path with mocked client |

## HTTPClient

### Injectable dependencies

| Parameter | Default when omitted | Test use |
| --- | --- | --- |
| `metrics` | `NULL_METRICS` (no-op) | `MagicMock(spec=MetricsTrackerProtocol)` |
| `template_service` | new `TemplateService()` | `MagicMock()` with `render_string` side effect |
| `session` | new `requests.Session()` | `MagicMock()` — stub `session.request` |

### Recommended pattern

```python
from unittest.mock import MagicMock

from pypost.core.http_client import HTTPClient

mock_session = MagicMock()
mock_ts = MagicMock()
mock_ts.render_string.side_effect = lambda s, v: s

client = HTTPClient(template_service=mock_ts, session=mock_session)
client.session.request.return_value = ...  # requests.Response stub
client.send_request(request_data, variables={})
```

Patching `client.session` after construction remains valid for legacy tests.

### Coverage

| Module | Class | Focus |
| --- | --- | --- |
| `tests/test_http_client.py` | `TestHTTPClientPrepareRequestKwargs` | `_prepare_request_kwargs` in isolation (URL, headers, params, body branches) |
| `tests/test_http_client.py` | `TestHTTPClientInjection` | TemplateService and session seams |
| `tests/test_http_client.py` | (other classes) | Transport, SSE, YAML body |

## MainWindow

`MainWindow` is a Qt composition root: it still constructs `StorageManager`, `RequestManager`,
presenters, and widgets internally. Full presenter extraction is tracked separately
([PYPOST-43](https://pypost.atlassian.net/browse/PYPOST-43)).

### Injectable dependencies (today)

| Parameter | Required | Test use |
| --- | --- | --- |
| `metrics` | yes | `MagicMock()` |
| `template_service` | yes | `MagicMock()` or real instance |
| `config_manager` | no | Inject to avoid disk I/O |
| `alert_manager` | no | Inject to assert alert propagation |

### Recommended pattern

Patch heavy collaborators at the **module under test** (`pypost.ui.main_window`), then
construct with injected services:

```python
with (
    patch("pypost.ui.main_window.StorageManager"),
    patch("pypost.ui.main_window.CollectionsPresenter") as mock_collections,
    patch("pypost.ui.main_window.MainWindow._build_layout"),
    patch("pypost.ui.main_window.wire_presenter_signals"),
    ...
):
    window = MainWindow(metrics=MagicMock(), template_service=MagicMock())
    mock_collections.return_value.refresh_tree.assert_called_once()
```

Cross-presenter signal wiring lives in `pypost/ui/main_window_signals.py` as
`wire_presenter_signals(window)`. Unit-test it directly with a `MagicMock` window — see
`tests/test_main_window_signals.py`. Integration tests that construct a real `MainWindow` still
exercise the full wiring path.

For signal/slot tests, mock presenters with real Qt widgets where needed — see
[gui_testing.md](gui_testing.md).

### Coverage

| Module | Test | Focus |
| --- | --- | --- |
| `tests/test_main_window.py` | `test_constructor_stores_injected_dependencies` | DI retention |
| `tests/test_main_window.py` | `test_startup_refreshes_tree_from_request_manager` | Startup orchestration |
| `tests/test_main_window.py` | `test_main_window_curl_copied_status_bar` | Signal wiring (integration) |
| `tests/test_main_window_signals.py` | `test_wire_presenter_signals_*` | `wire_presenter_signals` unit tests |

## RequestManager collection item strategies

`RequestManager.delete_collection_item` and `rename_collection_item` dispatch through
`DEFAULT_COLLECTION_ITEM_STRATEGIES` ([PYPOST-48](https://pypost.atlassian.net/browse/PYPOST-48)).
New tree item types register in the map without editing dispatch methods.

```python
from pypost.core.collection_item_strategies import CollectionItemStrategy
from pypost.core.request_manager import RequestManager

strategies = {
    "folder": CollectionItemStrategy(delete=..., rename=...),
}
manager = RequestManager(storage, item_strategies=strategies)
```

**Coverage:** `tests/test_collection_item_strategies.py`, `tests/test_request_manager_delete.py`.

## HTTPClientProtocol

`RequestService` depends on `HTTPClientProtocol` (structural typing) instead of the
concrete `HTTPClient` class. Production still constructs `HTTPClient` when no client is
injected.

```python
from pypost.core.http_client_protocol import HTTPClientProtocol

class RequestService:
    def __init__(self, http_client: HTTPClientProtocol | None = None):
        ...
```

```python
from unittest.mock import MagicMock

from pypost.core.http_client_protocol import HTTPClientProtocol

mock_http = MagicMock(spec=HTTPClientProtocol)
```

**Coverage:** `tests/test_http_client_protocol.py`, `TestRequestServiceInjection`.

## StorageInterface

`RequestManager`, environment presenters, migration services, and async storage workers depend
on `StorageInterface` instead of the concrete `StorageManager`. Production still constructs
`StorageManager` in `MainWindow`.

```python
from pypost.core.storage_interface import StorageInterface

class RequestManager:
    def __init__(self, storage_manager: StorageInterface, ...):
        self.storage = storage_manager
```

```python
from unittest.mock import MagicMock

from pypost.core.storage_interface import StorageInterface
from tests.helpers import FakeStorageManager

mock_storage = MagicMock(spec=StorageInterface)
# or
storage = FakeStorageManager([collection])
```

**Coverage:** `tests/test_storage_interface.py`, `tests/test_request_manager.py`.

## ExecuteRequestProtocol

`RequestWorker` and `MCPServerImpl` depend on `ExecuteRequestProtocol` (structural typing)
instead of the concrete `RequestService` class for the `execute` surface. Production still
constructs `RequestService` when no executor is injected.

```python
from pypost.core.execute_request_protocol import ExecuteRequestProtocol

class RequestWorker:
  def __init__(self, ...):
      self.service: ExecuteRequestProtocol = RequestService(...)
```

```python
from unittest.mock import MagicMock

from pypost.core.execute_request_protocol import ExecuteRequestProtocol

mock_executor = MagicMock(spec=ExecuteRequestProtocol)
```

**Coverage:** `tests/test_execute_request_protocol.py`.

## Out of scope (future tickets)

| Gap | Follow-up |
| --- | --- |
| `RequestWorker` accepts `RequestService` injection | [PYPOST-379](https://pypost.atlassian.net/browse/PYPOST-379) |
| MainWindow presenter decomposition | [PYPOST-43](https://pypost.atlassian.net/browse/PYPOST-43) |
| Full composition-root DI container | Backlog — not planned |

## Related

- [testing.md](testing.md) — suite timeouts and MCP testing
- [gui_testing.md](gui_testing.md) — Qt offscreen patterns
- [request_execution.md](request_execution.md) — execution pipeline
- [solid_audit.md](solid_audit.md) — PYPOST-40 audit summary
