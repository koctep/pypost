# Architecture: PYPOST-19 - MCP Integration

## Research
The Model Context Protocol (MCP) allows applications to provide context and tools to AI models.
Python SDK: `mcp`.
Transport: SSE (Server-Sent Events) is preferred for local servers.

Integration with PySide6 (Qt) requires managing the event loop. Since `mcp` uses `asyncio`, and Qt has its own loop, we need to coordinate them.
Option 1: Run `asyncio` loop in a separate thread (`QThread`).
Option 2: Use `qasync` to run `asyncio` on top of Qt loop.
**Choice**: Separate thread for the server to avoid blocking UI and minimize dependencies.

## Implementation Plan

1.  **Data Model**:
    -   Update `RequestData`: add `expose_as_mcp: bool = False`.
    -   Update `Environment` (or `AppSettings`): add `enable_mcp: bool = False` and `mcp_port: int = 8000`.

2.  **Core Logic (`pypost/core/mcp_server.py`)**:
    -   Class `MCPServerManager`: manages the server thread.
    -   Class `MCPServerImpl`: implementation of MCP server using SDK.
    -   Methods to start/stop server.
    -   Method `update_tools(requests)`: updates list of available tools.

3.  **UI**:
    -   `RequestWidget`: Add "MCP Tool" checkbox.
    -   `EnvironmentDialog` (or Settings): Add "Enable MCP Server" toggle.
    -   `MainWindow`:
        -   Initialize `MCPServerManager`.
        -   Start/stop server depending on settings.
        -   Update tools list when requests change.
        -   Indicator "MCP: ON/OFF".

## Architecture

### `MCPServerManager`
Responsible for the lifecycle of the server thread.
Signals:
- `status_changed(bool)`: Server status changed.
- `log_message(str)`: Logs.

### `MCPServerImpl`
Runs `FastMCP` or low-level server.
Since we need dynamic tool updates, `FastMCP` might be less flexible (decorators). Better to use low-level API or check if `FastMCP` supports dynamic tools.
*Research update*: `FastMCP` allows defining tools via decorators. For dynamic tools, we might need to register them dynamically or use a generic "execute_request" tool with an argument, but the requirement is "list of tools corresponding to requests".
*Solution*: Use `Server` from `mcp.server` and define `list_tools` and `call_tool` handlers manually.

### Interaction
1.  User enables MCP in Environment settings.
2.  `MainWindow` calls `mcp_manager.start(port, tools)`.
3.  `mcp_manager` starts a thread with `uvicorn` / `starlette` (for SSE) or uses `mcp` built-in serving if available.
    -   *Note*: MCP Python SDK usually runs over stdio or SSE. For SSE we need a web server (e.g., starlette/uvicorn).
4.  Agent connects to SSE endpoint.
5.  Agent calls `list_tools`. Server returns requests marked as `expose_as_mcp`.
6.  Agent calls `call_tool("request_name")`.
7.  Server executes request (using `HTTPClient` logic) and returns result.

## Q&A
-   **Dependencies?**
    -   `mcp`, `starlette`, `uvicorn`.
