# PYPOST-20: Technical Debt Analysis

## Shortcuts Taken

- **Hardcoded Routes**: Routes `/sse` and `/messages` are hardcoded in `MCPServerImpl`. If the MCP protocol specification changes, this will require code changes.
- **No Error Handling for Port Binding**: If the port is busy, `uvicorn` throws an exception that is caught in the thread, but the UI might not receive a clear error message (only "MCP: OFF" or log).

## Follow-up Tasks

- Improve error handling when starting the server (port in use).
