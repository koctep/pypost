# PYPOST-550: Dev Docs Update

## Summary

Documented MCP environment-variable injection for developers. Updated existing MCP and request
execution guides; no new top-level `doc/dev` file was needed because `mcp_integration.md` is
the canonical MCP developer reference.

## Files Updated

| File | Action |
| ---- | ------ |
| `doc/dev/mcp_integration.md` | Added EnvPresenter component, env-var injection flow, API/usage, configuration, troubleshooting |
| `doc/dev/request_execution.md` | Cross-reference to MCP merge behavior (PYPOST-550) |

## Documentation Highlights

### Overview

MCP `call_tool` now resolves active environment placeholders (`{{ base_url }}`, etc.) the same
way GUI sends do, while preserving `{{ mcp.request.* }}` agent arguments.

### Architecture

- **EnvPresenter** caches `_current_variables` on the main thread and registers
  `set_variable_supplier(lambda: dict(self._current_variables))`.
- **MCPServerManager** forwards the supplier to **MCPServerImpl**.
- **MCPServerImpl** snapshots env vars per `call_tool`, merges via
  `_merge_execution_variables`, passes result to **RequestService.execute()**.

### Key developer contracts

1. Supplier must be thread-safe (no Qt widget reads from MCP threadpool).
2. Merge order: `{**env_vars, "mcp": {"request": mcp_args}}` — `mcp` namespace wins.
3. Hidden variables: real values at execution; masking unchanged (UI/history only).
4. DEBUG log `mcp_execution_variables_merged` logs counts only (no secrets).

### Tests (reference)

- `tests/test_mcp_server_impl.py` — merge helper, supplier per call, GUI parity
- `tests/test_mcp_server_integration.py` — live SSE with env supplier
- `tests/test_env_presenter.py` — mock manager captures supplier registration

## Review

Autonomous sprint run — documentation reviewed against implementation in
`pypost/core/mcp_server_impl.py`, `pypost/core/mcp_server.py`, and
`pypost/ui/presenters/env_presenter.py`.

## Worklog

role: execution, step: 7, step_name: Dev Docs, tokens_used: (parent aggregate)
