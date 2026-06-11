# PYPOST-158: Test architecture

## Research

- PYPOST-367 documents that routing tests avoid live GET `/sse` because TestClient blocks on SSE
  streams. Structure and method guards are asserted instead.
- MCP SDK `SseServerTransport.connect_sse` requires `handle_sse_get` to return `Response()` after
  the ASGI stream ends; otherwise Starlette raises `TypeError` on client disconnect.
- PYPOST-155 moved 405 handling to Starlette `Route(methods=[...])` on the inner legacy app.
  Outer `Mount("/sse")` returns 405 for wrong methods on the mount path itself.

## Implementation Plan

1. Add `test_sse_get_returns_empty_response_after_connection_closes` — patch
   `SseServerTransport.connect_sse` with a short-lived context manager and `Server.run` with
   `AsyncMock`; assert GET `/` returns 200 with empty body (closure contract).
2. Expand method-guard tests in `TestMcpLegacySseModule`:
   - Non-GET methods on inner GET `/` → 405.
   - Non-POST methods on inner POST `/messages` → 405.
3. Add mounted-app helper: `Starlette(Mount("/sse", app=build_legacy_sse_app(...)))` and assert
   POST `/sse` and GET `/sse/messages` → 405.
4. Update `doc/dev/testing.md` MCP server unit test table.

## Test layout

```text
tests/test_mcp_legacy_sse.py
├── TestMcpLegacySseModule (existing import/structure guards)
└── TestMcpLegacySseHttpGuards (new)
    ├── test_sse_get_returns_empty_response_after_connection_closes
    ├── test_inner_app_rejects_non_get_on_sse_stream
    ├── test_inner_app_rejects_non_post_on_messages
    └── test_mounted_sse_app_rejects_wrong_methods
```

## Q&A

- **Q:** Why mock `connect_sse` instead of a live stream disconnect?
  - **A:** Starlette TestClient hangs on real SSE until full teardown; mocked transport exercises
    the same `handle_sse_get` → `Response()` contract without blocking CI.
