# PYPOST-727: Developer Documentation — pytest server test helpers

## Overview

`tests/test_mcp_server_manager.py` now uses native pytest instead of `unittest.TestCase`.
Polling loops are replaced by shared helpers.

## Helpers

| Helper | Module | Purpose |
| --- | --- | --- |
| `wait_until` | `tests/helpers/qt_wait.py` | Bounded Qt `processEvents` polling |
| `free_port` | `tests/helpers/mcp_live_server.py` | Ephemeral TCP port |
| `wait_for_port` | `tests/helpers/mcp_live_server.py` | Wait for server listen readiness |
| `qapp` | `tests/conftest.py` | Module-scoped `QApplication` fixture |

## Verification

```bash
make test PYTEST_ARGS="tests/test_mcp_server_manager.py -q"
```
