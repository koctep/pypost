# PYPOST-814: Architecture

## Problem

With `no_implicit_optional = true`, two classes of errors blocked protocol alignment:

1. **Implementation vs protocol:** `RequestService.execute` used `Dict[str, Any] = None` while
   `ExecuteRequestProtocol` declared `Dict[str, Any] | None = None`. Mypy rejected assigning
   `RequestService` to `ExecuteRequestProtocol` in `RequestWorker.service` and
   `MCPServerImpl._create_request_service()`.
2. **Worker constructor:** `RequestWorker.__init__` had `variables: dict = None` (implicit
   Optional).

## Protocol (source of truth)

| Parameter | Type |
| --- | --- |
| `request` | `RequestData` |
| `variables` | `Dict[str, Any] \| None = None` |
| `stream_callback` | `Callable[[str], None] \| None = None` |
| `stop_flag` | `Callable[[], bool] \| None = None` |
| `headers_callback` | `Callable[[int, Dict], None] \| None = None` |
| `collection_name` | `str \| None = None` |
| `request_name` | `str \| None = None` |
| `retry_callback` | `Callable[[int, int, ExecutionError], None] \| None = None` |
| `hidden_keys` | `set[str] \| None = None` |

## Changes

| File | Change | Task |
| --- | --- | --- |
| `pypost/core/request_service.py` | `execute`: four callback/variables params add `\| None` | PYPOST-813 |
| `pypost/core/qt/worker.py` | `__init__`: `variables: dict \| None = None` | PYPOST-814 |

No call-site or runtime logic changes — annotations only.

## Consumers verified

| Consumer | Usage | Result |
| --- | --- | --- |
| `RequestWorker` | `self.service = RequestService(...)` | Structural match after PYPOST-813 |
| `MCPServerImpl._create_request_service` | `return RequestService(...)` as `ExecuteRequestProtocol` | Clean after PYPOST-813 |
| `tests/test_execute_request_protocol.py` | `isinstance(..., ExecuteRequestProtocol)` | Passes |

## Baseline impact

| Metric | Before (PYPOST-813) | After (PYPOST-814) |
| --- | ---: | ---: |
| Total errors | 42 | 41 |
| `worker.py` errors | 1 | 0 |
| `mcp_server_impl.py` errors | 0 (resolved by PYPOST-813) | 0 |

Historical baseline (pre-PYPOST-813) included three protocol-related entries:

- `pypost/core/qt/worker.py:79:assignment`
- `pypost/core/qt/worker.py:40:assignment`
- `pypost/core/mcp_server_impl.py:228:return-value`

PYPOST-813 fixed the first and third; PYPOST-814 fixes the remaining worker constructor entry.
