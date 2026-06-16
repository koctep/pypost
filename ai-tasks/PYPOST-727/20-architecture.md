# PYPOST-727: Architecture

## Changes

| File | Change |
| --- | --- |
| `tests/helpers/qt_wait.py` | New `wait_until` helper — bounded `processEvents` polling |
| `tests/test_mcp_server_manager.py` | Migrate from unittest classes to pytest functions |
| `doc/dev/testing.md` | Document `wait_until` and `wait_for_port` helpers |

## Pattern

Replace inline deadline loops with:

```python
wait_until(lambda: manager.is_running(), message="MCP server did not start")
wait_for_port("127.0.0.1", port)
```

Use `caplog` instead of `unittest.TestCase.assertLogs`.
