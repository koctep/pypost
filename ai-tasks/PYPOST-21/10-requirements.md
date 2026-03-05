# PYPOST-21: Fix TypeError in SSE connection handling

## Goals

Fix the `TypeError: 'NoneType' object is not callable` error that occurs when working with SSE
endpoints (`/sse`, `/messages`). The error happens because Starlette incorrectly treats
`SSEEndpoint` and `MessagesEndpoint` as regular HTTP handlers (request/response) rather than ASGI
applications.

## User Stories

- As a developer, I want SSE connections to be established and closed correctly, without unhandled
  exceptions in server logs.
- As an API user, I want stable operation of `/sse` and `/messages` endpoints.

## Acceptance Criteria

- [ ] Endpoints `/sse` and `/messages` correctly handle connections and messages.
- [ ] No `TypeError: 'NoneType' object is not callable` error when closing connection.
- [ ] Starlette correctly recognizes handlers as ASGI applications.

## Task Description

### Problem

Current implementation (`pypost/core/mcp_server_impl.py`) uses `SSEEndpoint` and `MessagesEndpoint`
classes with `__call__` method for request handling.
However Starlette (`Route`) does not recognize them as ASGI applications and wraps them in
`request_response` mechanism. Since these methods do not return a `Response` object (they work
directly with `scope`, `receive`, `send`), the wrapper receives `None` and tries to call it,
causing the error.

Stack trace:
```
File "starlette/routing.py", line 76, in app
    await response(scope, receive, send)
TypeError: 'NoneType' object is not callable
```

### Proposed Solution

1. Change route registration:

   - Use `Mount` instead of `Route` for ASGI applications if applicable (but `Mount` uses prefix
     matching).
   - OR explicitly adapt classes so Starlette `is_asgi` returns `True`.
   - OR change method signatures or use a functional approach that Starlette recognizes.

Most reliable option: Use `WebSocketRoute` (if websocket) or ensure `Route` accepts them as ASGI.
For SSE (Server-Sent Events) this is regular HTTP but long-lived.
If we want to use low-level ASGI (as `SseServerTransport` does), we need to ensure Starlette does
not wrap it.

Starlette `is_asgi` check (usually) inspects the signature.
Perhaps explicitly typing `__call__` arguments or using a wrapper function would help.

Alternatively, we could simply return `Response` (e.g. `StreamingResponse`), but the `mcp` library
wants to manage the transport itself.

In `20-architecture.md` (which may be from previous attempts) a class-based solution was proposed
and implemented, but it does not work. We need to find why `is_asgi` returns False or use another
approach.

## Q&A

- **Q:** Why does `Route` not see ASGI?
  - **A:** Possibly due to class nesting or `inspect.signature` introspection quirks for instance
    methods.

- **Q:** Can `Mount` be used?
  - **A:** `Mount("/sse", app=SSEEndpoint(...))` will match `/sse` and `/sse/anything`. If that is
    acceptable, it is the simplest approach. SSE is usually mounted on a specific URL.
