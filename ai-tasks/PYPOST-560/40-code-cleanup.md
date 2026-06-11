# PYPOST-560: Code Cleanup

## Lint / Format

- `ruff check pypost/core/mcp_client_service.py tests/test_mcp_client_service.py` — no issues.
- Code style matches existing conventions (LF line endings, UTF-8 encoding, maximum 100 character line length, no trailing whitespace, final newline).

## Review Notes

- Cleaned up unused imports (removed `import asyncio` from `pypost/core/mcp_client_service.py` and `tests/test_mcp_client_service.py`).
- Replaced `asyncio.TimeoutError` references with standard Python `TimeoutError` which is raised by `anyio.fail_after`.
- Structured `_run_async` to use `async with ClientSession(...) as session` to ensure proper resource cleanup and prevent task group leaks.
