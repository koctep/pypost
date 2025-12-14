# Architecture: PYPOST-22 - Configurable MCP Server Host

## Research
`uvicorn`, used to run the Starlette app (MCP server), supports the `host` parameter.
We need to pass this parameter from settings to the server start method.

## Implementation Plan

1.  **Data Model**:
    -   Update `pypost/models/settings.py`: add `mcp_host: str = "127.0.0.1"`.

2.  **UI**:
    -   Update `pypost/ui/dialogs/settings_dialog.py`: add `QLineEdit` for `mcp_host`.

3.  **Server Logic**:
    -   Update `pypost/core/mcp_server.py` (`MCPServerManager.start_server`): accept `host` argument.
    -   Pass `host` to `uvicorn.run` inside the thread.

4.  **Integration**:
    -   Update `pypost/ui/main_window.py`: pass `settings.mcp_host` when starting the server.
    -   Update status label to show host.

## Architecture

### Changes in `MCPServerManager`

```python
def start_server(self, port: int, tools: list, host: str = "127.0.0.1"):
    # ...
    # inside thread:
    uvicorn.run(app, host=host, port=port)
```

### Changes in `MainWindow`

```python
self.mcp_manager.start_server(
    port=self.settings.mcp_port,
    tools=tools,
    host=self.settings.mcp_host
)
```
