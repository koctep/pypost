# Unit Testability Patterns (PYPOST-382)

## Overview

The PYPOST-40 audit flagged `RequestService`, `HTTPClient`, and `MainWindow` as hard to unit
test because dependencies were created internally. PYPOST-382 adds **constructor injection
seams** where practical and documents established mocking patterns. Metrics consumers now
depend on `MetricsTrackerProtocol` ([PYPOST-73](https://pypost.atlassian.net/browse/PYPOST-73));
broader protocol work continues in [PYPOST-46](https://pypost.atlassian.net/browse/PYPOST-46).

## Composition root

`main.py` creates shared services once and passes them into `MainWindow`:

| Service | Created in | Injected into |
| --- | --- | --- |
| `MetricsManager` (facade) | `main.py` | `MainWindow`, presenters, workers |
| `MetricsTrackerProtocol` | type hint at consumers | `MagicMock(spec=MetricsTrackerProtocol)` in tests |
| `MetricsRegistry` (counters) | inside `MetricsManager` | use directly in counter-only unit tests |
| `MetricsServer` (uvicorn/MCP) | inside `MetricsManager` | started via `metrics.start_server()` in `main.py` |
| `TemplateService` | `main.py` | `MainWindow`, `MCPServerManager`, `TabsPresenter` → workers |

See [PYPOST-378 dev notes](../../ai-tasks/PYPOST-378/70-dev-docs.md) for the full
`TemplateService` chain.

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

## RequestService

### Injectable dependencies

| Parameter | Default when omitted | Test use |
| --- | --- | --- |
| `metrics` | `NULL_METRICS` (no-op) | `MagicMock(spec=MetricsTrackerProtocol)`; assert `track_*` calls |
| `template_service` | `None` | `TemplateService()` for render paths |
| `history_manager` | `None` | `MagicMock(spec=HistoryManager)` |
| `alert_manager` | `None` | `MagicMock(spec=AlertManager)` |
| `http_client` | new `HTTPClient(...)` | `MagicMock()` — avoids network I/O |
| `mcp_client` | new `MCPClientService()` | `MagicMock()` — avoids MCP transport |

### Recommended pattern

Prefer constructor injection over post-construction attribute replacement:

```python
from unittest.mock import MagicMock

from pypost.core.request_service import RequestService
from pypost.core.template_service import TemplateService

mock_http = MagicMock()
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

## Out of scope (future tickets)

| Gap | Follow-up |
| --- | --- |
| `HTTPClient` protocol / interface | [PYPOST-46](https://pypost.atlassian.net/browse/PYPOST-46) |
| `RequestWorker` accepts `RequestService` injection | [PYPOST-379](https://pypost.atlassian.net/browse/PYPOST-379) |
| MainWindow presenter decomposition | [PYPOST-43](https://pypost.atlassian.net/browse/PYPOST-43) |
| Full composition-root DI container | Backlog — not planned |

## Related

- [testing.md](testing.md) — suite timeouts and MCP testing
- [gui_testing.md](gui_testing.md) — Qt offscreen patterns
- [request_execution.md](request_execution.md) — execution pipeline
- [solid_audit.md](solid_audit.md) — PYPOST-40 audit summary
