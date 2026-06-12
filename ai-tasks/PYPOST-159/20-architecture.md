# PYPOST-159: Mount + direct ASGI efficiency documentation

## Research

Starlette routing layers:

| Layer | Component | Wrapping | Notes |
| --- | --- | --- | --- |
| Outer app | `Mount(MCP_LEGACY_SSE_MOUNT_PATH)` | None — forwards ASGI to sub-app | Sub-app is a full `Starlette` instance |
| Inner app | `Route(..., MessagesEndpoint, methods=["POST"])` | Direct ASGI when endpoint is ASGI callable | `route.app` stays `MessagesEndpoint` instance |
| Inner app | `Route("/", handle_sse_get, methods=["GET"])` | `request_response` wrapper | Returns empty `Response` after `connect_sse` completes |

`Mount` never applies `request_response` — it treats `app` as an ASGI application. That is why
PYPOST-21 moved `/sse` and `/messages` from mistaken `Route` usage to `Mount` / direct ASGI.

`MessagesEndpoint` and `StreamableHTTPASGIApp` are class instances with ASGI `__call__`; Starlette
registers them without `request_response` (verified in `tests/test_mcp_asgi_compatibility.py`).

`handle_sse_get` is an async function returning `Response` — Starlette wraps it in
`request_response`. This is intentional: MCP `connect_sse` writes via ASGI `send`; after the
context exits, Starlette needs a response object to finalize the HTTP cycle.

## Implementation Plan

1. Add **Legacy SSE ASGI efficiency (PYPOST-159)** subsection to `doc/dev/mcp_integration.md`
   after existing legacy SSE routing bullets.
2. Extend `mcp_legacy_sse.py` module docstring with a short routing/efficiency summary.
3. No production routing changes; documentation only.

## Q&A

- **Q:** Is outer `Mount` more efficient than `Route` for the SSE sub-app?
  - **A:** Yes — `Mount` delegates without `request_response`. A `Route` around the whole sub-app
    would add an unnecessary adapter layer.
- **Q:** Is inner GET less efficient?
  - **A:** One `request_response` hop on GET only; negligible vs multi-minute SSE connection
    lifetime. POST `/messages` stays direct ASGI.
