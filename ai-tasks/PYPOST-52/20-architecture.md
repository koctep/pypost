# PYPOST-52: Architecture — Test Coverage for Refactoring Safety

## 1. Overview

Four new test files are introduced under `tests/`. A shared helper module is extracted
to avoid duplicating `FakeStorageManager` across test files. No production code is
changed; all changes are confined to the `tests/` directory.

```
tests/
├── helpers.py                         # NEW — shared FakeStorageManager
├── test_template_service.py           # NEW — TemplateService unit tests
├── test_request_manager.py            # NEW — RequestManager CRUD/index tests
├── test_http_client.py                # NEW — HTTPClient non-SSE tests
├── test_request_service.py            # NEW — RequestService orchestration tests
├── test_http_client_sse_probe.py      # EXISTING — unchanged
├── test_mcp_client_service.py         # EXISTING — unchanged
├── test_request_editor_method_tab_switch.py  # EXISTING — unchanged
└── test_request_manager_delete.py     # EXISTING — updated to import FakeStorageManager
```

---

## 2. Shared Test Helper (`tests/helpers.py`)

`FakeStorageManager` is currently defined inside `test_request_manager_delete.py`.
Moving it to a shared module avoids duplication and keeps the fake in sync if
`StorageManager`'s interface evolves.

```python
class FakeStorageManager:
    def __init__(self, collections=None):
        self._collections = collections or []
        self.saved_collections: list = []
        self.deleted_collection_names: list = []

    def load_collections(self):
        return list(self._collections)   # return copy to prevent mutation surprises

    def save_collection(self, collection):
        self.saved_collections.append(collection.name)

    def delete_collection(self, collection_name: str):
        self.deleted_collection_names.append(collection_name)
```

`test_request_manager_delete.py` is updated to:

```python
from tests.helpers import FakeStorageManager
```

This is a non-breaking change; the public interface stays identical.

---

## 3. `tests/test_template_service.py`

### Design Rationale

`TemplateService` wraps Jinja2 with no external I/O or side effects. Tests
instantiate a fresh `TemplateService()` in `setUp` so the global singleton is
never touched. No mocking is required.

### Test Class Layout

```
TestTemplateServiceRenderString
    test_render_known_variable
    test_render_unknown_variable_renders_empty_string
    test_render_none_returns_empty_string
    test_render_empty_string_returns_empty_string
    test_render_invalid_syntax_returns_original_content

TestTemplateServiceParse
    test_parse_valid_template_returns_ast
```

### Scenario Details

| Test | Input | Expected |
|---|---|---|
| `test_render_known_variable` | `"Hello {{ name }}"`, `{"name": "World"}` | `"Hello World"` |
| `test_render_unknown_variable_renders_empty_string` | `"{{ missing }}"`, `{}` | `""` (Jinja2 default Undefined) |
| `test_render_none_returns_empty_string` | `None`, `{}` | `""` (early-exit guard) |
| `test_render_empty_string_returns_empty_string` | `""`, `{}` | `""` |
| `test_render_invalid_syntax_returns_original_content` | `"{{ unclosed"`, `{}` | `"{{ unclosed"` (exception caught, original returned) |
| `test_parse_valid_template_returns_ast` | `"Hello {{ name }}"` | No exception; returns `jinja2.nodes.Template` |

### Mocking Requirements

None — `TemplateService` has no external dependencies.

---

## 4. `tests/test_request_manager.py`

### Design Rationale

`RequestManager` receives a `StorageManager` via constructor injection.
`FakeStorageManager` from `tests/helpers.py` is the only dependency replacement
needed. No network or disk I/O occurs.

`platformdirs` may be imported transitively through `storage.py`; the same stub
used in `test_request_manager_delete.py` is applied at the top of this file.

### Test Class Layout

```
TestRequestManagerCreate
    test_create_collection_returns_collection_with_uuid_id
    test_create_collection_persists_via_storage

TestRequestManagerSaveRequest
    test_save_new_request_appended_to_collection
    test_save_existing_request_updates_in_place
    test_save_request_unknown_collection_raises_value_error

TestRequestManagerFind
    test_find_request_returns_tuple_when_found
    test_find_request_returns_none_when_not_found

TestRequestManagerReload
    test_reload_collections_rebuilds_index_from_storage

TestRequestManagerGetCollections
    test_get_collections_returns_current_list

TestRequestManagerDeleteIndex
    test_delete_request_index_consistent_after_deletion
```

### Scenario Details

| Test | Setup | Action | Expected |
|---|---|---|---|
| `test_create_collection_returns_collection_with_uuid_id` | Empty storage | `create_collection("My API")` | `col.id` non-empty str, `col.name == "My API"` |
| `test_create_collection_persists_via_storage` | Empty storage | `create_collection("My API")` | `storage.saved_collections == ["My API"]` |
| `test_save_new_request_appended_to_collection` | Collection `c1` with 0 requests | `save_request(req, "c1")` | `collection.requests == [req]`, storage called |
| `test_save_existing_request_updates_in_place` | Collection `c1` with `req_v1` | `save_request(req_v2, "c1")` (same id) | `len(requests) == 1`, `requests[0] == req_v2` |
| `test_save_request_unknown_collection_raises_value_error` | Empty storage | `save_request(req, "unknown")` | `ValueError` raised |
| `test_find_request_returns_tuple_when_found` | `c1` contains `r1` | `find_request("r1")` | `(req, collection)` |
| `test_find_request_returns_none_when_not_found` | Empty | `find_request("missing")` | `None` |
| `test_reload_collections_rebuilds_index_from_storage` | Manager with empty storage | update `_collections`, call `reload_collections()` | new requests visible via `find_request` |
| `test_get_collections_returns_current_list` | `c1`, `c2` in storage | `get_collections()` | list of 2 `Collection` objects |
| `test_delete_request_index_consistent_after_deletion` | `c1` with `r1`, `r2` | `delete_request("r1")` | `find_request("r1")` is `None`, `find_request("r2")` still returns tuple |

### Mocking Requirements

- `FakeStorageManager` (from `tests/helpers`)
- `platformdirs` stub (same pattern as `test_request_manager_delete.py`)

---

## 5. `tests/test_http_client.py`

### Design Rationale

`HTTPClient` uses `self.session` (a `requests.Session` instance) for all network
calls. Tests replace `self.session` with a `MagicMock` in `setUp` after
constructing the client, then configure `session.request.return_value` per test.

`MetricsManager` is patched at the `pypost.core.http_client` module level to
eliminate Prometheus side effects. `template_service` is the real implementation
(stateless, no side effects) so it is not mocked.

A `_make_response` helper constructs a consistent fake `requests.Response`-like
`MagicMock` to reduce boilerplate across tests.

### Fake Response Helper

```python
def _make_response(status=200, headers=None, chunks=None):
    resp = MagicMock()
    resp.status_code = status
    resp.headers = {"Content-Type": "application/json", **(headers or {})}
    resp.iter_content.return_value = iter(chunks or ["body"])
    resp.close.return_value = None
    return resp
```

### Test Class Layout

```
TestHTTPClientSendRequest
    test_get_200_returns_response_data_with_correct_fields
    test_post_with_json_body_serialises_body_correctly
    test_template_variables_substituted_in_url
    test_template_variables_substituted_in_headers
    test_stop_flag_stops_streaming_and_returns_partial_body
    test_non_2xx_response_returns_correct_status_code
    test_connection_error_propagates
```

### Scenario Details

| Test | RequestData config | Mock | Expected |
|---|---|---|---|
| `test_get_200_returns_response_data_with_correct_fields` | `method=GET`, `url="http://x"` | 200, body `'{"ok":true}'` | `status_code=200`, `body='{"ok":true}'`, `elapsed_time > 0` |
| `test_post_with_json_body_serialises_body_correctly` | `method=POST`, `body='{"k":"v"}'`, `body_type='json'` | 200 | `session.request` called with `json={"k": "v"}`, no `data=` kwarg |
| `test_template_variables_substituted_in_url` | `url="{{ base }}/api"` | 200 | `session.request` called with `url="http://host/api"` |
| `test_template_variables_substituted_in_headers` | `headers={"X-Key": "{{ token }}"}` | 200 | `session.request` called with `headers={"X-Key": "abc123"}` |
| `test_stop_flag_stops_streaming_and_returns_partial_body` | GET, multi-chunk body | stop_flag returns True after first chunk | `response.close()` called; body is partial (first chunk only) |
| `test_non_2xx_response_returns_correct_status_code` | GET, 404 | 404 response | `ResponseData.status_code == 404` |
| `test_connection_error_propagates` | GET | `session.request` raises `requests.ConnectionError` | `ConnectionError` re-raised from `send_request` |

### Mocking Requirements

| Target | Patch path | How |
|---|---|---|
| `MetricsManager` | `pypost.core.http_client.MetricsManager` | `@patch` decorator or context manager |
| `requests.Session` | Replace `client.session` after construction | `client.session = MagicMock()` |

### setUp Pattern

```python
def setUp(self):
    self.metrics_patcher = patch("pypost.core.http_client.MetricsManager")
    self.metrics_patcher.start()
    self.client = HTTPClient()
    self.mock_session = MagicMock()
    self.client.session = self.mock_session

def tearDown(self):
    self.metrics_patcher.stop()
```

---

## 6. `tests/test_request_service.py`

### Design Rationale

`RequestService.execute()` orchestrates three collaborators: `HTTPClient`,
`MCPClientService`, and `ScriptExecutor`. All three are replaced with
`MagicMock` so no network calls or script execution occur.

`MetricsManager` (called inside `_execute_mcp`) is also patched.

### setUp Pattern

```python
def setUp(self):
    self.metrics_patcher = patch("pypost.core.request_service.MetricsManager")
    self.metrics_patcher.start()
    self.svc = RequestService()
    self.svc.http_client = MagicMock()
    self.svc.mcp_client = MagicMock()

def tearDown(self):
    self.metrics_patcher.stop()
```

### Shared Fixture

A `_make_response` helper builds a `ResponseData` with sensible defaults:

```python
def _make_response(status=200, body="OK"):
    return ResponseData(
        status_code=status, headers={}, body=body, elapsed_time=0.1, size=len(body)
    )
```

### Test Class Layout

```
TestRequestServiceExecuteHTTP
    test_execute_http_success_returns_execution_result
    test_execute_passes_variables_to_http_client
    test_execute_stream_callback_forwarded_to_http_client
    test_execute_headers_callback_forwarded_to_http_client

TestRequestServicePostScript
    test_execute_post_script_populates_logs_and_variables
    test_execute_post_script_error_sets_script_error_field

TestRequestServiceMCP
    test_execute_mcp_request_delegates_to_mcp_client
    test_execute_mcp_does_not_call_http_client
```

### Scenario Details

| Test | RequestData config | Mock config | Expected |
|---|---|---|---|
| `test_execute_http_success_returns_execution_result` | GET, `post_script=""` | `http_client.send_request` → `ResponseData(200)` | `result.response.status_code == 200`, `result.script_error is None` |
| `test_execute_passes_variables_to_http_client` | GET | variables `{"k": "v"}` | `send_request` called with `variables={"k": "v"}` |
| `test_execute_stream_callback_forwarded_to_http_client` | GET | `stream_callback=cb` | `send_request` called with `stream_callback=cb` |
| `test_execute_headers_callback_forwarded_to_http_client` | GET | `headers_callback=cb` | `send_request` called with `headers_callback=cb` |
| `test_execute_post_script_populates_logs_and_variables` | GET, `post_script="x=1"` | `ScriptExecutor.execute` → `({"x":1}, ["log"], None)` | `result.updated_variables == {"x":1}`, `result.script_logs == ["log"]` |
| `test_execute_post_script_error_sets_script_error_field` | GET, `post_script="bad"` | `ScriptExecutor.execute` → `({}, [], "SyntaxError")` | `result.script_error == "SyntaxError"` |
| `test_execute_mcp_request_delegates_to_mcp_client` | `method=MCP`, `url="http://x"` | `mcp_client.run` → `ResponseData(200)` | `result.response.status_code == 200` |
| `test_execute_mcp_does_not_call_http_client` | `method=MCP` | any | `http_client.send_request` never called |

### Mocking Requirements

| Target | Patch path / technique |
|---|---|
| `MetricsManager` | `patch("pypost.core.request_service.MetricsManager")` |
| `HTTPClient` | `self.svc.http_client = MagicMock()` |
| `MCPClientService` | `self.svc.mcp_client = MagicMock()` |
| `ScriptExecutor` | `patch("pypost.core.request_service.ScriptExecutor")` in relevant tests |

---

## 7. Import Guard for `platformdirs`

Any test file that imports (directly or transitively) from `pypost.core.storage`
must include the same `platformdirs` stub used in `test_request_manager_delete.py`:

```python
import sys, types

try:
    import platformdirs  # noqa: F401
except ModuleNotFoundError:
    _stub = types.ModuleType("platformdirs")
    _stub.user_data_dir = lambda app_name, app_author=None: "/tmp"
    sys.modules["platformdirs"] = _stub
```

Files that need this guard: `test_request_manager.py`.
Files that do **not** need it: `test_template_service.py`, `test_http_client.py`,
`test_request_service.py` (these do not import `storage.py` transitively,
assuming `MCPClientService` and `MetricsManager` are patched before import).

> **Note**: If `request_service.py` imports transitively pull in `storage.py`,
> add the guard to `test_request_service.py` as well. The Junior Engineer should
> verify by running `python -c "from pypost.core.request_service import RequestService"`
> in a clean environment.

---

## 8. Test Execution

Run all tests with:

```
python -m pytest tests/
```

Or via `make test` (sets `QT_QPA_PLATFORM=offscreen` for Qt tests).

No test should require network access, disk I/O, or external processes.

---

## 9. File Creation Checklist

| File | Action | Reason |
|---|---|---|
| `tests/helpers.py` | Create | Shared `FakeStorageManager` |
| `tests/test_template_service.py` | Create | TemplateService scenarios |
| `tests/test_request_manager.py` | Create | RequestManager CRUD/index scenarios |
| `tests/test_http_client.py` | Create | HTTPClient non-SSE scenarios |
| `tests/test_request_service.py` | Create | RequestService orchestration scenarios |
| `tests/test_request_manager_delete.py` | Update import | Use `from tests.helpers import FakeStorageManager` |

---

## 10. Constraints & Non-Goals

- No production code is modified.
- No `conftest.py` is introduced; existing `setUp`/`tearDown` pattern is preserved.
- No coverage configuration is added (out of scope).
- `MCPClientService` internals are not tested here (covered by `test_mcp_client_service.py`).
- `StorageManager` real implementation is never instantiated.
