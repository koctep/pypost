# PYPOST-1546: Code Cleanup Report

## Linter Fixes

- `make lint` passed (flake8 on `pypost/`, test lint baseline, markdown lint).
- Removed unused `_port2` binding in
  `tests/test_mcp_process_resource_limits_repro.py` after unpack rewrite.

## Formatting

- Helpers and repro tests kept within project line-length / style conventions.
- Process-mode call sites use a consistent `ports.release()` /
  `reserve.release()` line immediately before the first server start.

## Cleanup Actions

- `EphemeralPortReserve` now holds exclusive sockets via
  `allocate_bound_tcp_socket(..., reuse_addr=False)` instead of integer
  allocate-then-release.
- `verify_all_rebound` releases holders before probing rebind readiness.
- Repro module uses explicit `pytest.mark.timeout` (module + method).

## Quality Check

- `PYTEST_ARGS="tests/test_ephemeral_port_reserve_hold_repro.py tests/test_mcp_process_tool_refresh_repro.py tests/test_mcp_process_proxy_repro.py tests/test_mcp_process_reconfigure_repro.py tests/test_mcp_live_server_port_bind_repro.py" make test` — pass.
- `PYTEST_ARGS="tests/test_mcp_ipc_heartbeat_watchdog_repro.py tests/test_mcp_ipc_protocol_version_repro.py tests/test_mcp_process_resource_limits_repro.py" make test` — pass.
- `make lint` — pass.
