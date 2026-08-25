# PYPOST-1173: Technical Debt Analysis

## Shortcuts Taken

None specific to PYPOST-1173. The change is the wiring described in
`20-architecture.md`: `RequestService._execute_mcp` already resolved headers
and now passes `headers=resolved_headers` into `MCPClientService.run`, which
forwards that map to `create_mcp_http_client`. Empty and omitted maps are
normalized with `dict(headers or {})`. History and masking were left unchanged
because they already record `resolved.headers`.

Step 6 logs `header_count` only (not keys). Architecture allowed keys or
count; count is the stricter secret-safe choice and is not a shortcut.

## Code Quality Issues

None introduced by PYPOST-1173. In-scope modules stay small, typed, and
aligned with the proxy Streamable HTTP client factory pattern:

- `pypost/core/mcp_client_service.py` — optional `headers: dict[str, str] |
  None = None` on `run`; positional pass-through into `_run_with_timeout` /
  `_run_async`; factory call is `create_mcp_http_client(headers=...,
  timeout=...)` (no `headers=` on `streamable_http_client`).
- `pypost/core/request_service.py` — one extra keyword on the existing
  `mcp_client.run` call; template rendering is unchanged.

No new hardcoded timeouts, magic strings, or architecture-layer splits.

Pre-existing `make typecheck` baseline drift (not caused by this task, files
not modified here):

- `pypost/core/qt/websocket_stream_export_worker.py` —
  `StreamExportSnapshot` vs `MessageStream`
- `pypost/ui/dialogs/settings_dialog.py` — `layout()` callable vs `addWidget`

These are **NON-BLOCKER**. They predate PYPOST-1173. Do not expand this
ticket to refresh the mypy baseline.

## Missing Tests

None for the agreed PYPOST-1173 scope. Coverage matches architecture:

- User headers reach `create_mcp_http_client` — present in
  `tests/test_mcp_client_service.py`
  (`MCPClientServiceTests.test_run_passes_headers_to_create_mcp_http_client`)
- Resolved templated headers forwarded from `_execute_mcp` — present in
  `tests/test_request_service.py`
  (`TestRequestServiceMCP.test_execute_mcp_forwards_resolved_headers_to_mcp_client`)
- Empty / absent headers still call `run` — present in
  `tests/test_request_service.py`
  (`TestRequestServiceMCP.test_execute_mcp_forwards_empty_headers_to_mcp_client`)
- DEBUG start log is count-only (no values) — present:
  `test_run_logs_header_count_not_values`,
  `test_run_logs_zero_header_count_when_headers_omitted`

Both modules declare `pytestmark = pytest.mark.timeout(60)` (**NO BLOCKER**).

Intentionally out of scope (not missing): live MCP server with auth headers;
new History-masking cases (shared policy already covers `resolved_fields`);
MCP Client tab UI tests.

## Performance Concerns

None. The extra work is a small dict copy (`dict(headers or {})`) and
attaching those headers on the existing `httpx.AsyncClient`. No new
handshake, retry, or persistent session.

## Follow-up Tasks

No PYPOST-1173-specific follow-up is required for the header-forwarding
fix itself.

1. **NON-BLOCKER — pre-existing/flaky**
   - Node id:
     `tests/test_mcp_server_manager.py::test_update_tools_restarts_when_exposed_set_changes`
   - Repro: Step 6 `make test`; `EADDRINUSE` / port still busy after restart
   - Passed on re-run
   - Unrelated to PYPOST-1173 (dirty `mcp_server.py` / `port_allocation.py`
     independently)
   - Jira: [PYPOST-1178](https://pypost.atlassian.net/browse/PYPOST-1178)

2. **NON-BLOCKER — pre-existing**
   - `make typecheck` baseline drift in
     `websocket_stream_export_worker.py` and `settings_dialog.py`
     (see Code Quality Issues)
   - Observation only; do not invent extra scope on this ticket
   - Jira: [PYPOST-1179](https://pypost.atlassian.net/browse/PYPOST-1179)

Phase D of the orchestrator creates Jira issues. Step 7 does not.
