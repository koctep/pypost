# PYPOST-1362: Code Cleanup Report

## Linter Fixes

- Broke `_wait_until_not_running` signature across lines to satisfy flake8 E501 (≤100 cols).
- `make lint` passed (production flake8, test lint baseline, markdown/link checks).

## Formatting

- Matched existing registry test style (module `pytestmark`, helpers above tests).
- Production comments kept concise; no drive-by reformatting of `mcp_server.py`.

## Removed Code

- None. No dead imports after dropping an unused `MCPServerManager` import from an earlier
  monkeypatch draft of the red test.

## Refactoring

- `stop_server` joins against a local `server_thread` snapshot so worker clear-on-exit
  (PYPOST-1362) cannot race into `AttributeError` on `None.is_alive()`.
- Failed-start worker clears `_server_thread` when `current_thread()` is the server thread.

## Quality Check

- `make lint` — OK
- `make test PYTEST_ARGS='tests/test_mcp_server_registry.py tests/test_mcp_server_adaptive_join.py'` — OK
- Target nodes:
  - `test_failed_bind_is_reported_for_only_the_requested_instance` — PASS
  - `test_failed_bind_clears_server_thread_after_worker_exits` — PASS
- Timeouts: module `pytestmark = pytest.mark.timeout(120)` covers new/changed tests.

## Files Reviewed

- `pypost/core/qt/mcp_server.py`
- `tests/test_mcp_server_registry.py`
- `ai-tasks/PYPOST-1362/*.md`
