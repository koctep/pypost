# PYPOST-150: Code Cleanup

## Formatting

- New test module follows existing integration-test patterns (`pytestmark`, QApplication
  setup, bounded `_wait_for_listen`).

## Duplication

- Shared helpers live in one module rather than extending `test_mcp_server_manager.py` and
  `test_metrics_server_startup.py`, keeping host-bind coverage discoverable.

## Lint

- No production code changes; test-only diff.
