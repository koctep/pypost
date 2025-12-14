# Requirements: PYPOST-23 - Fix AttributeError in SSE Handling

## Goals
Fix a critical error preventing the MCP server from starting. The error `AttributeError: 'Starlette' object has no attribute 'add_route'` occurs when attempting to register SSE routes.

## User Stories
- As a developer, I want the MCP server to start without errors so I can test integration with AI agents.
- As a user, I want the "MCP: ON" indicator to reflect the actual working state of the server, not just the attempt to start it.

## Acceptance Criteria
- [ ] The application starts without `AttributeError` related to Starlette.
- [ ] The MCP server successfully binds to the port and accepts connections.
- [ ] The `/sse` endpoint is available and returns a 200 OK (or stream).

## Task Description
Investigate the cause of the error in `pypost/core/mcp_server_impl.py` and fix the route registration logic.
It seems that `Starlette` does not have an `add_route` method on the application instance if it is initialized incorrectly or if an outdated version is used (though Starlette usually has it). More likely, the issue is how `mcp` SDK creates the app or how we try to modify it.

### Technical Details
- **Component**: `MCPServerImpl`.
- **Library**: `starlette`, `mcp`.
