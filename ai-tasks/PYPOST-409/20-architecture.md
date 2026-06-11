# PYPOST-409: Architecture

## Current state (before)

```python
@dataclass
class ExecutionResult:
    response: ResponseData
    updated_variables: Dict[str, Any]
    script_logs: List[str]
    script_error: Optional[str]              # legacy duplicate
    execution_error: Optional[ExecutionError]  # canonical since PYPOST-400
```

`RequestService` populated both fields from `ScriptExecutor.execute()` return tuple.
`RequestWorker` and `MCPServerImpl` read `script_error` directly.

## Target state (after)

```python
@dataclass
class ExecutionResult:
    response: ResponseData
    updated_variables: Dict[str, Any]
    script_logs: List[str]
    execution_error: Optional[ExecutionError] = field(default=None)
```

Script failure detection pattern for callers:

```python
if (
    result.execution_error
    and result.execution_error.category == ErrorCategory.SCRIPT
):
    detail = result.execution_error.detail
```

## Change sites

| File | Change |
|------|--------|
| `pypost/core/request_service.py` | Drop `script_error` from dataclass and `ExecutionResult` construction |
| `pypost/core/worker.py` | Derive script error string from `execution_error` before `script_output` emit |
| `pypost/core/mcp_server_impl.py` | Append script error section from `execution_error.detail` |
| `tests/test_request_service.py` | Assert on `execution_error` only |
| `tests/test_worker.py`, `tests/test_worker_race.py` | Remove `script_error=` kwargs |
| `tests/test_mcp_server_impl.py` | Build `execution_error` in `_exec_result` helper |
| `doc/dev/request_execution.md` | Document script error via `execution_error` |

## Unchanged

- `ScriptExecutor.execute()` still returns `(vars, logs, error_str)` — local variable only.
- `RequestWorker.script_output` signal signature `(list, str)` unchanged; UI layer unchanged.
- Metrics: `track_request_error(ErrorCategory.SCRIPT)` unchanged.
- `tabs_presenter._on_script_output` still receives `(logs, err)` from worker signal.

## Data flow (script failure)

```
ScriptExecutor.execute() → error_str
    → RequestService wraps ExecutionError(SCRIPT, detail=error_str)
    → ExecutionResult(execution_error=...)
    → RequestWorker reads execution_error.detail → script_output signal
    → MCPServerImpl reads execution_error.detail → tool response text
```
