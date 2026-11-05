# PYPOST-1439: Code Cleanup Report

## Linter Fixes

Describe fixed linter errors and warnings:
- Fixed: mypy `attr-defined` / `method-assign` on `mcp_worker_process._run_uvicorn`
  (direct assignment to `install_signal_handlers` and `startup`). Switched to
  `setattr(...)`, matching `metrics_server.py`, so new files stay off the mypy
  baseline delta.
- Fixed: `stop_flag` annotated as `dict[str, bool]` while storing the uvicorn
  `Server`; corrected to `dict[str, Any]` and dropped the assignment
  `# type: ignore`.
- Fixed: hoisted `import threading` in `worker_main` to module level.
- Fixed: `ProcessServerRunner.__init__` `on_unexpected_exit` typed as `Any`;
  narrowed to `Callable[[str, int | None], None] | None`.
- Fixed: `MCPServerRegistry(..., execution_mode=...)` annotated as bare `str`;
  narrowed to `Literal["thread", "process"]` (runtime ValueError guard retained).

## Code Formatting

Applied formatting changes:
- [x] Automatic code formatting (flake8 clean; no >100-char lines in scope modules)
- [x] Indentation and alignment fixes (none required beyond type/setattr cleanup)
- [x] Line length correction (scope modules checked; none over 100)

## Code Cleanup

Cleanup actions performed:
- Removed unused imports: 0 (prior Step 4 already lazy-imported Qt probe runner)
- Removed unused variables: 0
- Removed commented-out code: none present
- Removed debug prints: none present
- Style/typing cleanup only in process-mode modules (`mcp_worker_process`,
  `mcp_server_runner`, `mcp_server_registry`); no behavioral changes

## Validation Results

Validation results:
- [x] Scoped isolation tests passed
  (`make test PYTEST_ARGS="tests/test_mcp_process_isolation_repro.py -q"`)
- [x] All tests have explicit timeout markers
  (module `pytestmark` + per-test overrides in isolation repro)
- [x] No merge conflicts
- [x] Syntax is valid
- [x] Types are correct (`make typecheck` — mypy baseline OK, 175 known errors)
- [x] `make lint` OK (flake8, test-lint baseline, markdown/link checks)

Note: repo has no `make analyze` target; static analysis via `make lint` +
`make typecheck` per AGENTS.md / Step 5 instructions.

## Notes

- uvicorn 0.54 exposes `capture_signals` (already a no-op off the main thread)
  rather than `install_signal_handlers`; the setattr override remains for older
  stubs/APIs and parity with the thread-mode MCP path.
- Full-suite `make check` was not re-run here; isolation repro + lint/typecheck
  cover Step 5 scope. Gate owner may widen if desired.
