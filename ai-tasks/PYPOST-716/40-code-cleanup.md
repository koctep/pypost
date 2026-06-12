# PYPOST-716: Code Cleanup

## Lint / Format

- No new linter issues in changed files.
- Verified file compliance with PEP 8 and project standards.
- Removed unused imports (such as `MagicMock` in `tests/test_mcp_server_manager.py`).
- Trailing whitespace removed and proper final newlines ensured.

## Refactoring

- Removed `_occupy_port` socket blockers from `test_port_busy_emits_start_failed` in `tests/test_mcp_server_manager.py` and `tests/test_metrics_server_startup.py`.
- Replaced socket-occupy setup with clean `unittest.mock.patch` calls mocking `uvicorn.Server.serve` raising `OSError(errno.EADDRINUSE, "Address already in use")`.
- Cleaned up unneeded socket handles and simplified exception/clean exit assertions on macOS.

## Worklog

role: execution, step: 4, step_name: Code Cleanup, tokens_used: 500
