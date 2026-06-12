# PYPOST-160: Module-level legacy SSE endpoints

## Verified state

Refactor completed in PYPOST-156. Shared module `pypost/core/mcp_legacy_sse.py`:

```text
SSEEndpoint          # module-level ASGI callable
MessagesEndpoint     # module-level ASGI callable
build_legacy_sse_app(server, messages_path=..., debug=False) -> Starlette
```

`MCPServerImpl` wiring:

```text
create_app() → Starlette(routes=[mcp_route, Mount(..., app=_create_sse_app())])
_create_sse_app() → build_legacy_sse_app(self.server, debug=True)
```

No nested endpoint classes remain in `mcp_server_impl.py`.

## Files (PYPOST-156)

| File | Role |
| ---- | ---- |
| `pypost/core/mcp_legacy_sse.py` | Shared endpoints + factory |
| `pypost/core/mcp_server_impl.py` | Delegates to `build_legacy_sse_app` |
| `pypost/core/metrics_server.py` | Delegates to `build_legacy_sse_app` |
| `tests/test_mcp_legacy_sse.py` | Isolated endpoint/routing tests |

## Q&A

- **Q:** Why close PYPOST-160 separately from PYPOST-156?
  - **A:** PYPOST-160 was filed from PYPOST-21 tech-debt before PYPOST-156 landed; this task
    confirms acceptance criteria and closes the duplicate issue.
