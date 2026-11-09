# PYPOST-1541: Code Cleanup Report

## Linter Fixes

- `make lint` passed (flake8 on `pypost/`, test lint baseline, markdown lint).

## Formatting

- Helpers and repro tests kept within project line-length / style conventions.
- No unused imports left in changed modules.

## Cleanup Actions

- Removed allocate-then-release probe duplication by routing `allocate_tcp_port`
  through `allocate_bound_tcp_socket`.
- `LiveMCPServer.stop()` clears thread/server/socket handles so bind retries do
  not leak prior uvicorn workers.
- Repro module uses explicit `pytest.mark.timeout` (module + method).

## Quality Check

- `PYTEST_ARGS="tests/test_mcp_live_server_port_bind_repro.py tests/test_mcp_server_integration.py::TestMCPServerIntegration::test_call_tool_substitutes_jira_mcp_json_body" make test` — pass.
- `make lint` — pass.
