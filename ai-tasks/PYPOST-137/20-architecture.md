# PYPOST-137: Architecture

## Current behavior (verified)

```
User selects env in UI
        │
        ▼
EnvPresenter._on_env_changed
        ├── EnvVariableSnapshot.update(vars, hidden_keys)
        ├── start/stop MCP based on enable_mcp
        └── emit env_* signals

MCPServerImpl.call_tool (any thread)
        │
        ▼
_build_execution_variables → variable_supplier()  # fresh snapshot each call
        │
        ▼
RequestService.execute(request, merged_vars)
```

Per-call freshness is implemented in PYPOST-550; this task adds clarity and observability
only.

## Changes

### Documentation

- `doc/dev/mcp_integration.md` — **Active environment binding** section: behavior table,
  agent implications, troubleshooting row.
- `doc/mcp_integration.md` — user-facing **Active environment** note and troubleshooting row.
- Fix stale `_current_variables` references → `EnvVariableSnapshot`.

### Observability

`EnvPresenter._on_env_changed`:

1. Capture `previous = itemData(_current_env_index)` and `mcp_was_running = is_running()`
   before MCP lifecycle updates.
2. After processing, if `mcp_was_running` and env **id** changed, call
   `_track_mcp_active_env_changed(previous, selected)`.

New metric: `mcp_active_env_changes_total` via `track_mcp_active_env_changed()`.

New log: `mcp_active_env_changed prev_env_id=… new_env_id=…` (INFO, ids only).

### Tests

- `test_env_presenter.py` — metric on env switch while running; no metric on same-env refresh.
- `test_metrics_registry.py` — counter scrape assertion.
- Rely on existing `test_call_tool_invokes_variable_supplier_per_call` for call-time proof.

## Non-goals

- MCP `notifications` to clients on env change.
- Locking environment for duration of agent session.
- Changing restart-on-tool-catalog-change behavior.
