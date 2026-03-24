# PYPOST-400: Observability — Stabilize Post Publishing API Error Handling

## 1. Review Findings

The implementation was reviewed against the architecture in `20-architecture.md`. Two categories of
gaps were found: a missing logger in `mcp_client_service.py` and missing log calls at two error
sites in `request_service.py`.

### Gap A — `mcp_client_service.py`: no logger, no source-level log entries

The module had no `import logging` and no `logger`. Errors raised by `MCPClientService.run()` were
caught silently by `RequestService.execute()` (which only tracked metrics). This meant an MCP
connection failure produced a Prometheus counter increment and a UI message, but nothing in the
application log between those two points.

### Gap B — `request_service.py`: `except ExecutionError` block had no log call

Lines 124–133 caught `ExecutionError` from both `http_client.send_request()` and
`mcp_client.run()`. HTTP errors were already logged in `http_client.py` before being raised, but
MCP errors (Gap A) were not. Adding a log at the catch site ensures every `ExecutionError` that
causes `execute()` to return an error result is recorded regardless of where it originated.

### Gap C — `request_service.py`: TEMPLATE guard raised without logging

The Jinja2 template render guard (lines 107–114) raised `ExecutionError(TEMPLATE)` without a log
call. The error propagated up to `RequestWorker`, which logged it, but having a source-level log
with the offending URL template and the Jinja2 exception detail makes diagnosis faster.

---

## 2. Changes Made

### `pypost/core/mcp_client_service.py`

| What | Detail |
|------|--------|
| Added `import logging` | stdlib import |
| Added module-level `logger` | `logging.getLogger(__name__)` → `pypost.core.mcp_client_service` |
| `DEBUG` on operation start | `mcp_operation_start url=… operation=…` — one entry per call |
| `ERROR` before `asyncio.TimeoutError` raise | `mcp_operation_timeout url=… operation=… timeout=…` |
| `ERROR` before general `Exception` raise | `mcp_operation_failed url=… operation=… category=… detail=…` |
| `DEBUG` on success | `mcp_operation_success url=… operation=… elapsed=…` |

### `pypost/core/request_service.py`

| What | Detail |
|------|--------|
| `ERROR` in `except ExecutionError` block | `request_execution_failed method=… url=… category=… detail=…` |
| `ERROR` in TEMPLATE guard before raise | `template_render_failed url=… detail=…` |

---

## 3. Metrics (unchanged — already complete)

The `MetricsManager` counters added during implementation cover all error paths:

| Counter | Labels | Incremented by |
|---------|--------|----------------|
| `request_errors_total` | `category` | `RequestService.execute()` on `ExecutionError` catch (HTTP/MCP/SCRIPT) |
| `history_record_errors_total` | — | `RequestService.execute()` on history append failure |

No additional counters are needed. The `category` label (`network`, `timeout`, `template`,
`script`, `unknown`) gives per-category break-down at the Prometheus level.

---

## 4. Log Level Policy

| Scenario | Level | Rationale |
|----------|-------|-----------|
| MCP operation start | `DEBUG` | High-frequency; off by default |
| MCP operation success | `DEBUG` | High-frequency; off by default |
| MCP timeout | `ERROR` | Indicates a real failure |
| MCP connection/other failure | `ERROR` | Indicates a real failure |
| Template render failure | `ERROR` | Likely a configuration error |
| `ExecutionError` caught in `execute()` | `ERROR` | Any undelivered request |
| History record failure | `ERROR` | Already present pre-PYPOST-400 |
| Request cancellation | `INFO` | Expected user action, not an error |

---

## 5. Files Modified

| File | Change Type |
|------|-------------|
| `pypost/core/mcp_client_service.py` | Added logger + 4 log calls |
| `pypost/core/request_service.py` | Added 2 log calls |
