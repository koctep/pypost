# PYPOST-155: Route-based method filtering for legacy SSE

## Current state (before)

Inner legacy SSE Starlette app (`_create_sse_app`):

```text
Mount("/messages", app=MessagesEndpoint)   # all methods hit ASGI app
Route("/", endpoint=handle_sse_get, methods=["GET"])
```

`MessagesEndpoint` checked `scope["method"] != "POST"` and sent manual 405 ASGI messages.
`SSEEndpoint` duplicated GET filtering even though the outer `Route` already restricted methods.

## Target state

```text
Route("/messages", endpoint=MessagesEndpoint, methods=["POST"])
Route("/", endpoint=handle_sse_get, methods=["GET"])
```

`MessagesEndpoint` remains a pure ASGI callable delegating to
`SseServerTransport.handle_post_message` — required because the MCP SDK writes directly to `send`.

`SSEEndpoint` drops redundant GET guard; Starlette returns 405 for non-GET on `/`.

Outer app still uses `Mount(MCP_LEGACY_SSE_MOUNT_PATH, ...)` to host the legacy sub-app under
`/sse`; that mount has no method filter (POST to `/sse` correctly returns 405 via routing).

## Files

| File | Change |
| ---- | ------ |
| `pypost/core/mcp_server_impl.py` | Route + simplified endpoints |
| `pypost/core/metrics_server.py` | Mirror layout |
| `tests/test_mcp_server_impl.py` | Assert POST Route on `/messages` |
| `doc/dev/mcp_integration.md` | Document routing |

## Q&A

- **Q:** Why keep ASGI classes instead of request/response handlers?
  - **A:** `connect_sse` and `handle_post_message` are ASGI-level; wrapping in `Response` would
    break streaming semantics.
