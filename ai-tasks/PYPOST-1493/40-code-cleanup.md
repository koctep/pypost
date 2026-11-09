# PYPOST-1493: Code Cleanup Report

## Linter Fixes

- `make lint` passed (flake8 on `pypost/`, test lint baseline, markdown lint,
  relative link check).
- No unused imports introduced; harness logging uses module `logger`.

## Formatting

- `wait_for_stderr` and test updates kept within project line-length / style
  conventions.
- Lock-order comment documents why stderr notify runs outside `_stderr_lock`.

## Cleanup Actions

- Replaced bare `get_stderr()` asserts in stderr collection tests with bounded
  `wait_for_stderr`.
- Left `get_stderr()` as a non-blocking snapshot API (no hidden waits).

## Quality Check

- `make test PYTEST_ARGS='tests/test_mcp_stdio_harness.py -v'` — pass.
- `make lint` — pass.
- Module `pytestmark = pytest.mark.timeout(30)` unchanged (covers new repro).
