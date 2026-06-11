# PYPOST-137: Dev Docs

## Updated files

| File | Change |
| --- | --- |
| `doc/dev/mcp_integration.md` | Added **Active environment binding (PYPOST-137)**; fixed `EnvVariableSnapshot` naming; troubleshooting row |
| `doc/mcp_integration.md` | User **Active environment** section; troubleshooting for mid-session credential changes |

## Key points for developers

- MCP `call_tool` invokes `variable_supplier()` on every call — no stale env cache in
  `MCPServerImpl`.
- `EnvVariableSnapshot` is updated on the main thread in `_on_env_changed`.
- Environment **identity** change while `MCPServerManager.is_running()` emits
  `mcp_active_env_changed` and `mcp_active_env_changes_total`.

## Operator guidance

Documented in user-facing `doc/mcp_integration.md`: avoid switching environments during
active agent sessions when stable credentials/hosts are required.
