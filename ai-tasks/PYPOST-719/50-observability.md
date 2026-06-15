# PYPOST-719: Observability

## Coverage Metric

`pypost/core/mcp_server.py` coverage raised from ~38% (audit baseline) to 99%.

Only line 163 (`original_exit(code)` when code==0 in `thread_exit`) remains uncovered —
it requires uvicorn to call `sys.exit(0)` inside a background thread, an event that
cannot be triggered deterministically without running a real server.

## Test Count

Total tests: 1430 (up from 1423 before this task).
