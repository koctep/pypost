# PYPOST-45 Architecture: Replace `template_service` Global with Constructor Injection

## Overview

This document describes the design for removing the module-level `template_service` singleton
and threading `TemplateService` through constructors via optional dependency injection. The
change is a pure refactor: no public APIs change and all callers continue to work without
modification.

---

## Current State

```
template_service.py         → exposes module-level `template_service = TemplateService()`
    ↑ imported by
http_client.py              → uses global in _prepare_request_kwargs + send_request
request_service.py          → uses global in _execute_mcp
mcp_server_impl.py          → uses global in _extract_mcp_variables
```

### Dependency graph (before)

```
TemplateService  ──(global import)──▶  HTTPClient
                 ──(global import)──▶  RequestService
                 ──(global import)──▶  MCPServerImpl
```

---

## Target State

```
TemplateService  ──(constructor param)──▶  HTTPClient
                                                ▲
RequestService  ──(constructor param, passes own instance)──▶  HTTPClient
                                                ▲
MCPServerImpl  ──(constructor param, passes own instance)──▶  RequestService
```

### Dependency graph (after)

```
MCPServerImpl(template_service=ts)
    └─▶ RequestService(metrics=m, template_service=ts)
            └─▶ HTTPClient(metrics=m, template_service=ts)
```

All three classes own `self._template_service`. If no value is passed, each creates its own
`TemplateService()` as the default (autonomous default pattern).

---

## Design Decisions

### Autonomous default (not shared default)
Each class creates `TemplateService()` when `None` is supplied rather than importing a
shared fallback. This avoids re-introducing a module-level object. Each instance gets its
own `jinja2.Environment`, which is cheap to create and isolates side-effects.

### Optional parameter with `None` sentinel
Using `template_service: TemplateService | None = None` (rather than
`template_service: TemplateService = TemplateService()`) avoids creating a `TemplateService`
at import time as a default argument—which would be equivalent to the current global.

### No changes to `MCPServerManager` or `RequestWorker`
Both callers use positional-keyword `metrics=metrics`. The new `template_service` parameter
defaults to `None`, so no call-site changes are needed (REQ-5).

---

## File-by-File Changes

### 1. `pypost/core/template_service.py`

**Change**: Remove lines 35–36 (comment + global assignment).

```python
# REMOVE:
# Global instance
template_service = TemplateService()
```

No other change. The class definition is unchanged.

---

### 2. `pypost/core/http_client.py`

**Remove import**:
```python
# REMOVE:
from pypost.core.template_service import template_service
```

**Add import** (class only):
```python
from pypost.core.template_service import TemplateService
```

**Update `__init__`**:
```python
def __init__(self, metrics: MetricsManager | None = None,
             template_service: TemplateService | None = None):
    self.session = requests.Session()
    self._metrics = metrics
    self._template_service = template_service if template_service is not None else TemplateService()
```

**Replace all 6 usages** of the bare `template_service` name with `self._template_service`:

| Location | Old | New |
|---|---|---|
| `_prepare_request_kwargs` line 26 | `template_service.render_string(...)` | `self._template_service.render_string(...)` |
| `_prepare_request_kwargs` lines 30–31 | `template_service.render_string(...)` × 2 | `self._template_service.render_string(...)` × 2 |
| `_prepare_request_kwargs` lines 36–37 | `template_service.render_string(...)` × 2 | `self._template_service.render_string(...)` × 2 |
| `_prepare_request_kwargs` line 40 | `template_service.render_string(...)` | `self._template_service.render_string(...)` |
| `send_request` line 145 | `template_service.render_string(...)` | `self._template_service.render_string(...)` |

---

### 3. `pypost/core/request_service.py`

**Remove import**:
```python
# REMOVE:
from pypost.core.template_service import template_service
```

**Add import** (class only):
```python
from pypost.core.template_service import TemplateService
```

**Update `__init__`**:
```python
def __init__(self, metrics: MetricsManager | None = None,
             template_service: TemplateService | None = None):
    self._metrics = metrics
    self._template_service = template_service if template_service is not None else TemplateService()
    self.http_client = HTTPClient(metrics=self._metrics, template_service=self._template_service)
    self.mcp_client = MCPClientService()
```

**Replace 2 usages** in `_execute_mcp` (lines 33–34):
```python
# OLD:
url = template_service.render_string(request.url, variables)
body = template_service.render_string(request.body, variables).strip()
# NEW:
url = self._template_service.render_string(request.url, variables)
body = self._template_service.render_string(request.body, variables).strip()
```

---

### 4. `pypost/core/mcp_server_impl.py`

**Remove import**:
```python
# REMOVE:
from pypost.core.template_service import template_service
```

**Add import** (class only):
```python
from pypost.core.template_service import TemplateService
```

**Update `__init__`**:
```python
def __init__(self, name: str = "pypost-server", metrics: MetricsManager | None = None,
             template_service: TemplateService | None = None):
    self.server = Server(name)
    self.tools_map: Dict[str, RequestData] = {}
    self._metrics = metrics
    self._template_service = template_service if template_service is not None else TemplateService()
    self.request_service = RequestService(metrics=self._metrics,
                                          template_service=self._template_service)
    # Register handlers
    self.server.list_tools()(self.list_tools)
    self.server.call_tool()(self.call_tool)
```

**Replace 1 usage** in `_extract_mcp_variables` (line 132):
```python
# OLD:
ast = template_service.parse(content)
# NEW:
ast = self._template_service.parse(content)
```

---

### 5. `tests/test_http_client.py` — new tests (append only)

Add a new test class `TestHTTPClientInjection`:

```python
class TestHTTPClientInjection(unittest.TestCase):
    def test_injected_template_service_is_used_not_default(self):
        """A TemplateService passed at construction is the one called during send_request."""
        mock_ts = MagicMock()
        mock_ts.render_string.side_effect = lambda s, v: s  # passthrough
        client = HTTPClient(template_service=mock_ts)
        client.session = MagicMock()
        client.session.request.return_value = _make_response(200, chunks=["ok"])
        req = RequestData(method="GET", url="http://x/{{ path }}")
        client.send_request(req, variables={"path": "items"})
        mock_ts.render_string.assert_called()

    def test_no_injection_creates_own_template_service(self):
        """HTTPClient() with no template_service still works (uses internal default)."""
        client = HTTPClient()
        client.session = MagicMock()
        client.session.request.return_value = _make_response(200)
        req = RequestData(method="GET", url="http://x")
        result = client.send_request(req)
        self.assertEqual(200, result.status_code)
```

---

### 6. `tests/test_request_service.py` — new tests (append only)

Add a new test class `TestRequestServiceInjection`:

```python
class TestRequestServiceInjection(unittest.TestCase):
    def test_injected_template_service_forwarded_to_http_client(self):
        """TemplateService passed to RequestService is the same instance in http_client."""
        from pypost.core.template_service import TemplateService
        ts = TemplateService()
        svc = RequestService(template_service=ts)
        self.assertIs(ts, svc._template_service)
        self.assertIs(ts, svc.http_client._template_service)

    def test_no_injection_creates_own_template_service(self):
        """RequestService() with no template_service still works."""
        svc = RequestService()
        self.assertIsNotNone(svc._template_service)
```

---

## Sequence Diagram: Object Creation (after)

```
Caller
  │
  ├─▶ MCPServerImpl(metrics=m)
  │       │  self._template_service = TemplateService()  [default]
  │       └─▶ RequestService(metrics=m, template_service=self._template_service)
  │               │  self._template_service = <same instance>
  │               └─▶ HTTPClient(metrics=m, template_service=self._template_service)
  │                       │  self._template_service = <same instance>
  │                       └─▶ (uses self._template_service for all rendering)
  │
  └─▶ MCPServerImpl(metrics=m, template_service=custom_ts)
          │  self._template_service = custom_ts
          └─▶ RequestService(metrics=m, template_service=custom_ts)
                  └─▶ HTTPClient(metrics=m, template_service=custom_ts)
```

---

## Acceptance Criteria Mapping

| Criterion | Satisfied by |
|---|---|
| AC-1: no `from pypost.core.template_service import template_service` | Removing all 3 imports |
| AC-2: no `template_service = TemplateService()` in template_service.py | Removing lines 35–36 |
| AC-3: all three classes store `self._template_service` | __init__ changes above |
| AC-4: all existing tests pass unmodified | Default `None` preserves old call signatures |
| AC-5: new test confirms injected mock is invoked in `send_request` | `TestHTTPClientInjection.test_injected_template_service_is_used_not_default` |

---

## Out of Scope

- Internal implementation of `TemplateService` (`render_string`, `parse`)
- Adding `template_service` to `MCPServerManager` or `RequestWorker` call sites
- Replacing the `jinja2.Environment`
- Any non-template rendering logic in the affected files
