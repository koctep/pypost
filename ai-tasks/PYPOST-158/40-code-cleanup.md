# PYPOST-158: Code Cleanup

## Static analysis

- No production code changes; test-only diff.
- New imports (`contextlib`, `unittest.mock`, `anyio`, `SseServerTransport`, `Mount`) follow
  existing test module style.

## Cleanup actions

- Consolidated duplicate 405 assertions into parametrized-style loops per path.
- No unused imports; line length within 100 characters.

## Tests

- `.venv/bin/python -m pytest tests/test_mcp_legacy_sse.py -v` — all tests pass.
