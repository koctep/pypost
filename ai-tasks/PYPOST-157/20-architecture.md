# PYPOST-157: MessagesEndpoint response cleanup

## Research

- PYPOST-155 replaced `Mount("/messages", ...)` with `Route(..., methods=["POST"])`, removing
  in-endpoint 405 handling and `_send_response`.
- PYPOST-156 moved endpoints to `pypost/core/mcp_legacy_sse.py` for reuse by both MCP servers.
- MCP SDK `SseServerTransport.handle_post_message` remains ASGI-level and must receive
  `scope` / `receive` / `send` directly.

## Implementation Plan

1. Confirm `MessagesEndpoint.__call__` delegates only to `handle_post_message`.
2. Keep `starlette.responses.Response` at module scope for `handle_sse_get` (GET stream wrapper).
3. Add a unit test that inspects `MessagesEndpoint` source for removed manual response helpers.
4. Document the routing vs ASGI split in `doc/dev/mcp_integration.md`.

## Architecture

```text
build_legacy_sse_app
├── Route(POST /messages) → MessagesEndpoint (pure ASGI → handle_post_message)
├── Route(GET /)          → handle_sse_get (Request handler → Response() at module import)
└── Starlette 405 for wrong methods on /messages (no endpoint code)
```

| Component | Response responsibility |
| --------- | --------------------- |
| Starlette `Route` | 405 for non-POST on messages path |
| `MessagesEndpoint` | None — delegates to MCP SDK |
| `handle_sse_get` | Returns empty `Response()` after SSE ASGI completes |

## Q&A

- **Q:** Why not convert `MessagesEndpoint` to a `Request` → `Response` handler?
  - **A:** `handle_post_message` writes via ASGI `send`; a Response wrapper would fight streaming
    semantics and duplicate SDK behavior.
