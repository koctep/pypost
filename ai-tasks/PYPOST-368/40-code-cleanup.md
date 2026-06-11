# PYPOST-368: Code Cleanup

## Lint / Format

- `flake8 tests/test_mcp_server_integration.py` — no issues.
- Module follows existing MCP test conventions (`pytestmark`, `unittest.TestCase`, helpers).

## Review Notes

- No production code changes; test-only diff.
- Shared helpers (`_free_port`, `_exec_result`) are local to the integration module to avoid
  premature abstraction.
