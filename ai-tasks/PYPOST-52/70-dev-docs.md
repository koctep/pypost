# PYPOST-52: Developer Documentation

## Purpose

PYPOST-52 establishes a unit-test safety net for the four core backend modules
(`TemplateService`, `RequestManager`, `HTTPClient`, `RequestService`) before the
planned refactoring work in PYPOST-43–51. No production code was changed.

---

## New Files

| File | Description |
|---|---|
| `tests/helpers.py` | Shared `FakeStorageManager` used by all `RequestManager` tests |
| `tests/test_template_service.py` | Unit tests for `TemplateService` (Jinja2 rendering) |
| `tests/test_request_manager.py` | Unit tests for `RequestManager` CRUD and index operations |
| `tests/test_http_client.py` | Unit tests for `HTTPClient` non-SSE request paths |
| `tests/test_request_service.py` | Unit tests for `RequestService` orchestration |
| `pytest.ini` | Pytest configuration: verbose output, short tracebacks, live logging |

## Modified Files

| File | Change |
|---|---|
| `Makefile` | Added `pytest-cov` to `venv-test`; added `test-cov` target |
| `tests/test_request_manager_delete.py` | Replaced inline `FakeStorageManager` with import from `tests.helpers` |

---

## Running the Tests

```bash
# Run all tests (standard)
make test

# Run with coverage report (terminal + HTML)
make test-cov
# HTML report written to htmlcov/index.html

# Run a single test file
.venv/bin/python -m pytest tests/test_template_service.py -v

# Run a single test case
.venv/bin/python -m pytest tests/test_http_client.py::TestHTTPClientSendRequest::test_get_200_returns_response_data_with_correct_fields -v
```

---

## Test Architecture

### Shared Helper: `tests/helpers.py`

`FakeStorageManager` is an in-memory substitute for `StorageManager`. It
satisfies the interface expected by `RequestManager` without touching the disk.

```
FakeStorageManager(collections=None)
  .load_collections()          → returns copy of internal list
  .save_collection(collection) → records collection.name in .saved_collections
  .delete_collection(name)     → records name in .deleted_collection_names
```

Use in tests:

```python
from tests.helpers import FakeStorageManager

storage = FakeStorageManager([collection])
manager = RequestManager(storage)
# assert storage.saved_collections == ["My API"]
```

---

### `test_template_service.py`

No mocking required. Each test class creates a fresh `TemplateService()` in
`setUp` to avoid shared singleton state.

Key behaviours tested:
- Known variables are substituted correctly.
- Unknown variables render as empty string (Jinja2 `Undefined` default).
- `None` and `""` inputs return `""` without raising.
- Invalid Jinja2 syntax returns the original content unchanged.
- `parse()` returns a `jinja2.nodes.Template` AST on valid input.

---

### `test_request_manager.py`

Uses `FakeStorageManager` for all storage interactions. A `platformdirs` stub
is applied at module level because `pypost.core.storage` imports `platformdirs`
at import time:

```python
try:
    import platformdirs
except ModuleNotFoundError:
    _stub = types.ModuleType("platformdirs")
    _stub.user_data_dir = lambda app_name, app_author=None: "/tmp"
    sys.modules["platformdirs"] = _stub
```

Key behaviours tested: `create_collection`, `save_request` (new and update),
`find_request`, `reload_collections`, `get_collections`, and post-deletion index
consistency.

---

### `test_http_client.py`

`MetricsManager` is patched at module level before `HTTPClient` is constructed.
The `requests.Session` is replaced with a `MagicMock` after construction to
intercept all network calls without connecting to a real server.

```python
def setUp(self):
    self.metrics_patcher = patch("pypost.core.http_client.MetricsManager")
    self.metrics_patcher.start()
    self.client = HTTPClient()
    self.client.session = MagicMock()   # intercept all network calls
```

The module-level `_make_response(status, headers, chunks)` helper builds a
consistent fake `requests.Response` MagicMock for reuse across tests.

Key behaviours tested: GET 200, POST JSON serialisation, template substitution
in URL and headers, stop-flag streaming abort, non-2xx status, connection error.

---

### `test_request_service.py`

`RequestService`'s three collaborators (`HTTPClient`, `MCPClientService`,
`ScriptExecutor`) are replaced with `MagicMock`. `MetricsManager` is patched.

```python
def setUp(self):
    self.metrics_patcher = patch("pypost.core.request_service.MetricsManager")
    self.metrics_patcher.start()
    self.svc = RequestService()
    self.svc.http_client = MagicMock()
    self.svc.mcp_client  = MagicMock()
```

`ScriptExecutor` is patched inline (via `with patch(...)`) only in post-script
tests so the patch does not affect unrelated test classes.

Key behaviours tested: HTTP success path, variable/callback forwarding,
post-script log/variable population, post-script error propagation, MCP
delegation, MCP does not invoke `HTTPClient`.

---

## Pytest Configuration (`pytest.ini`)

| Setting | Effect |
|---|---|
| `-v` | Print each test name and result |
| `--tb=short` | Compact traceback on failure |
| `log_cli = true` | Live log output during test run |
| `log_cli_level = WARNING` | Captures `WARNING`+`ERROR` from production code |
| `log_format` / `log_date_format` | Standardised timestamps for correlating logs to tests |

---

## Known Limitations / Future Work

See `60-review.md` for the full tech debt list. The two highest-priority items
before beginning PYPOST-43–51 refactoring are:

1. **Fragile positional `call_args` indexing** in `test_request_service.py` —
   switch to keyword-argument inspection (`call_args.kwargs`).
2. **`ScriptExecutor` mock targets class, not instance** — verify and correct
   the patch target to `mock_executor.return_value.execute`.

Additionally, a CI pipeline (GitHub Actions) should be added as a follow-up
ticket to run `make test` automatically on every push and pull request.
