# PYPOST-727: Migrate unittest server tests to pytest

## Goals

Convert `tests/test_mcp_server_manager.py` from `unittest.TestCase` to native pytest style,
replacing manual polling loops with shared helpers.

## Definition of Done

- `test_mcp_server_manager.py` uses pytest functions (no `unittest.TestCase`).
- Shared `wait_until` helper in `tests/helpers/qt_wait.py` for bounded Qt polling.
- Reuses `free_port` / `wait_for_port` from `tests/helpers/mcp_live_server.py`.
- All tests pass with explicit timeout markers.
