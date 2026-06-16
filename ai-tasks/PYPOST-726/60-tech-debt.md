# PYPOST-726: Technical Debt Analysis

## Shortcuts Taken

None. The implementation uses the standard asyncio pattern (cancel all pending tasks,
`gather` with `return_exceptions=True`) already used internally by `asyncio.run()`.

## Code Quality Issues

None blocking. `drain_pending_tasks` is a single, well-documented helper in
`server_bind.py` alongside `format_bind_error`, keeping uvicorn lifecycle helpers
co-located.

## Missing Tests

Coverage is adequate for this scope:

- Unit tests for `drain_pending_tasks` (pending, no-op, cleanup path).
- Regression tests on `MCPServerManager._run_uvicorn` and `MetricsServer._run_uvicorn`.
- Full suite passes with no destroyed-task warnings.

No integration test explicitly exercises `LiveMCPServer` teardown with warning capture;
production call sites are covered by the `_run_uvicorn` regression tests and the harness
mirrors the same `try/finally` pattern.

## Performance Concerns

None. Cancellation interrupts long `sleep` polls immediately; shutdown adds negligible
overhead (one `gather` on typically one stray task).

## Follow-up Tasks

- **Pre-existing `StarletteDeprecationWarning`** in `test_mcp_asgi_compatibility.py`
  (`httpx` vs `httpx2`) — unrelated to this ticket; track under general test-harness
  maintenance if it becomes a gate failure.
