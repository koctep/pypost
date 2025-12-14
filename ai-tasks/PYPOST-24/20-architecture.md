# PYPOST-24: Fix TypeError in SSE connection handling

## Research

1.  **Starlette Routing and ASGI**: Starlette determines if an endpoint is an ASGI application using
    `starlette._utils.is_asgi`. If `is_asgi` returns `False`, Starlette wraps the endpoint in
    `request_response`, which expects a `Response` return value.
2.  **`is_asgi` issue**: For class instances `is_asgi` may return `False` if the `__call__`
    signature does not look exactly like ASGI (`scope`, `receive`, `send`).
3.  **Mount vs Route**: `Route` is for HTTP endpoints and has wrapping logic. `Mount` is for
    mounting ASGI sub-applications. Using `Mount` for a single endpoint (e.g. `/sse`) is a valid
    pattern if we want to work in pure ASGI mode.

## Implementation Plan

1.  **Change route registration**:
    Use `Mount("/sse", app=SSEEndpoint(...))` instead of `Route("/sse", endpoint=SSEEndpoint(...))`.
    Same for `/messages`.

2.  **Implementation details**:
    In `pypost/core/mcp_server_impl.py`:
    - Import `Mount` from `starlette.routing`.
    - Replace `Route` with `Mount` for `/sse` and `/messages`.

3.  **Explanation**: `Mount` expects an ASGI application. A class instance with method
    `__call__(self, scope, receive, send)` is a valid ASGI application. `Mount` does not try to
    wrap it in request/response cycle, which should fix the expected `Response` return value issue
    (and subsequent `await None` error).

## Architecture

### Changes in `pypost/core/mcp_server_impl.py`

Before:
```python
routes=[
    Route("/sse", endpoint=SSEEndpoint(self.server, sse)),
    Route("/messages", endpoint=MessagesEndpoint(sse), methods=["POST"]),
],
```

After:
```python
routes=[
    Mount("/sse", app=SSEEndpoint(self.server, sse)),
    Mount("/messages", app=MessagesEndpoint(sse)),
],
```
*Note*: `Mount` does not accept a `methods` parameter. For `/messages` we need to ensure only POST
requests are handled. This can be done inside `MessagesEndpoint` or keep `Route` but rewrite the
endpoint to return `Response` (harder, since `mcp` works with ASGI), or use `WebSocketRoute` (not
suitable, this is not websocket).
However, `SseServerTransport.handle_post_message` likely expects POST.
If using `Mount` for `/messages`, it will intercept all methods. Better to check the method inside
`MessagesEndpoint`.

Alternative for `/messages`: Keep `Route` but wrap `handle_post_message` to return `Response`. But
`handle_post_message` writes directly to `send`.
If `mcp` writes to `send`, it must be an ASGI application.

**Refined plan**:
1. Use `Mount` for `/sse`. This fixes the long-lived connection and `None` return issue.
2. For `/messages`:
   - Either `Mount("/messages", ...)` and check `scope['method'] == 'POST'`.
   - Or figure out why `Route` does not see ASGI.

Starlette `is_asgi` check is fairly simple. It inspects the signature.
```python
def is_asgi(app: typing.Any) -> bool:
    if inspect.isclass(app):
        return False
    if hasattr(app, "__call__"):
        app = app.__call__
    ...
```
Most likely the issue was that `SSEEndpoint` was a class *instance* inside a method.

**The Mount solution seems most reliable for integrating low-level ASGI applications (such as
wrappers over `mcp`).**

## Q&A

- **Q:** Will `Mount` work correctly for the exact path `/sse`?
  - **A:** Yes, `Mount("/sse", ...)` matches requests starting with `/sse`. This includes `/sse`
    (with empty path remainder).
