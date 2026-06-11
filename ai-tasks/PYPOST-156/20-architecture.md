# PYPOST-156: Module-level legacy SSE endpoints

## Current state (before)

`MCPServerImpl._create_sse_app` and `MetricsServer._create_sse_app` each defined nested
`SSEEndpoint` and `MessagesEndpoint` classes plus duplicate Starlette route tables.

## Target state

New module `pypost/core/mcp_legacy_sse.py`:

```text
SSEEndpoint          # module-level ASGI callable
MessagesEndpoint     # module-level ASGI callable
build_legacy_sse_app(server, messages_path=..., debug=False) -> Starlette
```

Callers:

```text
MCPServerImpl._create_sse_app  → build_legacy_sse_app(self.server, debug=True)
MetricsServer._create_sse_app  → build_legacy_sse_app(self.mcp_server)
```

Outer apps unchanged: `Mount(MCP_LEGACY_SSE_MOUNT_PATH, app=...)`.

## Files

| File | Change |
| ---- | ------ |
| `pypost/core/mcp_legacy_sse.py` | New shared endpoints + factory |
| `pypost/core/mcp_server_impl.py` | Delegate to `build_legacy_sse_app` |
| `pypost/core/metrics_server.py` | Delegate to `build_legacy_sse_app` |
| `tests/test_mcp_legacy_sse.py` | Isolated endpoint/routing tests |
| `doc/dev/mcp_integration.md` | Document shared module |

## Q&A

- **Q:** Why a new module instead of module-level classes in each server file?
  - **A:** Eliminates duplication; matches `mcp_transport_routes.py` single-source pattern.
