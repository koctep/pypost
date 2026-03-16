# PYPOST-52: Add Test Coverage for Refactoring Safety

## Summary

Add unit test coverage for the four core backend modules — `RequestService`, `HTTPClient`,
`RequestManager`, and `TemplateService` — before undertaking major refactoring work
(MainWindow decomposition, DI for singletons, etc.). Tests must prevent regressions
when PYPOST-43 through PYPOST-51 are implemented.

## Goals

- Establish a safety net that catches regressions introduced during planned refactoring.
- Achieve meaningful (not exhaustive) coverage of the critical execution path in each module.
- Keep tests fast, isolated, and deterministic (no real network calls, no disk I/O).

## User Stories

- As a developer, I want unit tests for `RequestService` so that I can refactor its
  internals without accidentally breaking request execution or script handling.
- As a developer, I want unit tests for `HTTPClient` so that I can change transport
  and session logic without breaking HTTP behaviour.
- As a developer, I want unit tests for `RequestManager` so that I can introduce DI
  without breaking collection/request CRUD operations.
- As a developer, I want unit tests for `TemplateService` so that I can swap the
  templating backend without silently breaking variable substitution.

## Scope

### In Scope

#### TemplateService (`pypost/core/template_service.py`)

| Scenario | Expected Result |
|---|---|
| Render string with known variable | Variable is substituted correctly |
| Render string with unknown variable | Original placeholder kept (Jinja2 undefined) |
| Render `None` / empty string | Returns empty string, no exception |
| Render invalid Jinja2 syntax | Returns original content, no exception |
| `parse()` on valid template string | Returns Jinja2 AST without error |

#### RequestManager (`pypost/core/request_manager.py`)

Existing tests cover delete/rename. New tests should cover the remaining surface:

| Scenario | Expected Result |
|---|---|
| `create_collection(name)` | Returns `Collection` with UUID id, persists via storage |
| `save_request(request, collection_id)` | Request stored in correct collection, storage called |
| `find_request(request_id)` — found | Returns `(RequestData, Collection)` tuple |
| `find_request(request_id)` — not found | Returns `None` |
| `reload_collections()` | Re-reads from storage, rebuilds index |
| `get_collections()` | Returns current in-memory list |
| `delete_request` index rebuild | Index is consistent after deletion |

#### HTTPClient (`pypost/core/http_client.py`)

Existing tests cover SSE probing. New tests should cover:

| Scenario | Expected Result |
|---|---|
| Standard GET request (200, JSON body) | `ResponseData` with correct status, body, elapsed |
| Standard POST with JSON body | Body serialised, `Content-Type: application/json` sent |
| Template variables substituted in URL | Rendered URL used, not raw template string |
| Template variables substituted in headers | Rendered headers sent |
| `stop_flag` returns `True` during stream | Streaming stops, partial body returned |
| Non-2xx response (e.g. 404) | `ResponseData` returned with correct status code |
| Connection error / timeout | Exception surfaced as `ResponseData` with status 0 or raises |

#### RequestService (`pypost/core/request_service.py`)

| Scenario | Expected Result |
|---|---|
| `execute()` with HTTP request — success | Returns `ExecutionResult` with `ResponseData`, empty errors |
| `execute()` with HTTP request — post-script runs | `script_logs` and `updated_variables` populated |
| `execute()` with HTTP request — post-script error | `script_error` non-empty, result still returned |
| `execute()` with MCP request (`expose_as_mcp=True`) | Delegates to `MCPClientService`, returns result |
| Variables passed through to `HTTPClient` | HTTPClient receives the same variables dict |
| `stream_callback` forwarded to `HTTPClient` | Callback invoked for streamed responses |
| `headers_callback` forwarded | Callback invoked with status code and headers dict |

### Out of Scope

- UI components (`MainWindow`, widgets)
- `MCPClientService` internals (already tested in `test_mcp_client_service.py`)
- `ScriptExecutor` internals (tested indirectly through `RequestService`)
- `StorageManager` disk I/O
- Integration / end-to-end tests
- Performance benchmarks

## Definition of Done

- [ ] New test file(s) committed under `tests/`.
- [ ] All new tests pass with `python -m pytest tests/` (no failures, no errors).
- [ ] No real HTTP connections or file I/O in any test (mocked via `unittest.mock`).
- [ ] Each module listed above has at least the scenarios in the table above covered.
- [ ] `TemplateService` and `RequestService` each have a dedicated test file.
- [ ] `HTTPClient` and `RequestManager` test files extended (or new files added) to cover
  the missing scenarios above.

## Technical Notes

- Use `unittest` + `unittest.mock.patch` / `MagicMock` (consistent with existing tests).
- Mock `MetricsManager` wherever it is injected or imported to avoid side effects.
- `FakeStorageManager` pattern (already in `test_request_manager_delete.py`) should be
  reused or extended for `RequestManager` tests.
- `TemplateService` uses a global singleton `template_service`; tests should instantiate
  a fresh `TemplateService()` directly to avoid cross-test state.
- `RequestService.execute()` wraps `HTTPClient` — mock `HTTPClient.send_request` to
  control responses without network calls.

## Related Tickets

- PYPOST-43 through PYPOST-51: Refactoring tasks that this test coverage enables safely.
- PYPOST-40: SOLID and maintainability audit (labels reference this).
