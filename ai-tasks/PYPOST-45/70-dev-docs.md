# PYPOST-45 Developer Documentation: `TemplateService` Constructor Injection

## What Changed

The module-level singleton `template_service = TemplateService()` was removed from
`pypost/core/template_service.py`. `TemplateService` is now injected via constructors
across the three classes that consume it.

---

## Dependency Chain

```
MCPServerImpl(template_service=ts)
    └─▶ RequestService(metrics=m, template_service=ts)
            └─▶ HTTPClient(metrics=m, template_service=ts)
```

Each class exposes an optional `template_service: TemplateService | None = None` parameter.
When `None` is passed (the default), the class creates its own `TemplateService()` instance
and propagates it downward. This means the full chain shares a single instance when the
top-level constructor receives one.

---

## Constructor Signatures (after PYPOST-45)

```python
# pypost/core/http_client.py
class HTTPClient:
    def __init__(self, metrics: MetricsManager | None = None,
                 template_service: TemplateService | None = None): ...

# pypost/core/request_service.py
class RequestService:
    def __init__(self, metrics: MetricsManager | None = None,
                 template_service: TemplateService | None = None): ...

# pypost/core/mcp_server_impl.py
class MCPServerImpl:
    def __init__(self, name: str = "pypost-server", metrics: MetricsManager | None = None,
                 template_service: TemplateService | None = None): ...
```

All three store the resolved instance as `self._template_service`.

---

## Common Usage Patterns

### Default (no injection — production callers unchanged)

```python
# MCPServerManager, RequestWorker — no change needed
server = MCPServerImpl(metrics=metrics)
svc = RequestService(metrics=metrics)
```

Each call creates one `TemplateService` at the top level, propagated down automatically.

### Inject a custom or mock `TemplateService`

```python
from pypost.core.template_service import TemplateService
from pypost.core.mcp_server_impl import MCPServerImpl

custom_ts = TemplateService()          # or a subclass / mock
server = MCPServerImpl(metrics=m, template_service=custom_ts)
# server._template_service is custom_ts
# server.request_service._template_service is custom_ts
# server.request_service.http_client._template_service is custom_ts
```

### Testing with a mock

```python
from unittest.mock import MagicMock
from pypost.core.http_client import HTTPClient

mock_ts = MagicMock()
mock_ts.render_string.side_effect = lambda s, v: s   # passthrough
client = HTTPClient(template_service=mock_ts)
```

---

## Logging

All three constructors emit a `DEBUG`-level log line indicating whether an injected or
default-created instance is in use, including the Python object `id()`:

```
DEBUG pypost.core.http_client: HTTPClient: using injected TemplateService id=140234567890
DEBUG pypost.core.http_client: HTTPClient: created default TemplateService id=140234567891
```

These are silent at the default `WARNING` level. Enable with `--log-level=DEBUG` or by
configuring a `DEBUG` handler in the application's logging config.

When all three `id()` values are the same, the full chain is sharing a single instance
(injection in use). When they differ, each class owns its own default instance.

---

## Files Changed

| File | Change |
|---|---|
| `pypost/core/template_service.py` | Removed global `template_service = TemplateService()`. Added `import logging` and `logger`. Replaced `print()` with `logger.error()`. |
| `pypost/core/http_client.py` | Replaced global import with class import. Added `template_service` constructor param and `self._template_service`. Added `DEBUG` log. Replaced 6 bare `template_service.*` calls with `self._template_service.*`. |
| `pypost/core/request_service.py` | Same as `http_client.py`. Added `logger`. Forwards `template_service` to `HTTPClient`. Replaced 2 bare calls in `_execute_mcp`. |
| `pypost/core/mcp_server_impl.py` | Same as `http_client.py`. Added `logger`. Forwards `template_service` to `RequestService`. Replaced 1 bare call in `_extract_mcp_variables`. |
| `tests/test_http_client.py` | Appended `TestHTTPClientInjection` (2 tests). |
| `tests/test_request_service.py` | Appended `TestRequestServiceInjection` (2 tests). |

---

## Out of Scope

- `MCPServerManager` and `RequestWorker` call sites — no changes required.
- `TemplateService` internal implementation (`render_string`, `parse`).
- Replacing `jinja2.Environment` or adding custom filters/globals.
