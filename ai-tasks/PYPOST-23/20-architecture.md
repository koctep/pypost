# Architecture: PYPOST-23 - Fix AttributeError in SSE Handling

## Research
The error `AttributeError: 'Starlette' object has no attribute 'add_route'` suggests that the object we are trying to add a route to is not what we think it is, or the method is named differently.

In `MCPServerImpl.create_app`:
```python
self.app = Starlette(debug=True)
# ...
self.app.add_route("/sse", handle_sse)
```
This code is correct for Starlette.

However, if `mcp.server.fastmcp` or another abstraction is used which returns its own object wrapping Starlette, then `add_route` might be missing.

**Investigation**:
The code uses `mcp.server.Server`.
The implementation of `create_app` creates a `Starlette` app.

**Possible Cause**:
Conflict between `starlette` versions or incorrect import.
Or `self.app` is overwritten somewhere.

**Solution**:
Ensure `Starlette` is initialized correctly.
Pass routes to the constructor `Starlette(routes=[...])` instead of `add_route` if dynamic addition fails (though it should work).

## Implementation Plan

1.  **Refactor `create_app`**:
    -   Define `handle_sse` and `handle_messages` functions.
    -   Create `Route` objects.
    -   Initialize `Starlette` with the list of routes.

```python
from starlette.applications import Starlette
from starlette.routing import Route

# ...
routes = [
    Route("/sse", endpoint=handle_sse, methods=["GET"]),
    Route("/messages", endpoint=handle_messages, methods=["POST"])
]
self.app = Starlette(debug=True, routes=routes)
```

2.  **Verify**:
    -   Run the application.
    -   Check logs.
