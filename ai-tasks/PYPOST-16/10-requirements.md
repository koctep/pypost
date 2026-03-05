# Requirements: PYPOST-16 - Model Context Protocol (MCP) Integration

## Goals
Integrate support for Model Context Protocol (MCP) into PyPost. This will allow PyPost to act as an MCP server, exposing saved requests as tools for AI agents (e.g., Claude, Cursor). This enables agents to execute HTTP requests configured in PyPost directly from their context.

## User Stories
- As a user, I want to be able to enable the MCP server in PyPost settings so that my AI agent can connect to it.
- As a user, I want to mark specific requests as "Expose as Tool" so that only selected requests are available to the agent.
- As a user, I want the agent to be able to call my requests, passing parameters (if any), and receive the response.
- As a user, I want to see the status of the MCP server (running/stopped) in the interface.

## Acceptance Criteria
- [ ] **MCP Server**:
    - Implemented MCP server supporting SSE (Server-Sent Events) transport.
    - Server runs on a configurable port (default 8000).
- [ ] **Data Model**:
    - `RequestData` has an `expose_as_mcp` (bool) field.
    - `Environment` has `enable_mcp` (bool) field.
- [ ] **UI**:
    - Checkbox "Expose as MCP Tool" in request editor.
    - Checkbox "Enable MCP Server" in environment settings (or global settings).
    - Server status indicator in the main window.
- [ ] **Functionality**:
    - When the server is enabled, it exposes a list of tools corresponding to requests with `expose_as_mcp=True`.
    - Tool name corresponds to request name (sanitized).
    - Tool execution performs the HTTP request using PyPost logic (including variable substitution).
    - Execution result is returned to the agent.

## Task Description
Implement an MCP server inside PyPost using the `mcp` SDK (python).

### Technical Details
- **Protocol**: MCP (Model Context Protocol).
- **Transport**: SSE (easiest for local integration).
- **SDK**: `mcp` (Python).
- **Integration**: The server must run in a separate thread/process or use `asyncio` loop, integrated with the Qt event loop (e.g., via `qasync` or running in a separate thread).

## Q&A
- **How to handle parameters?**
    - For the first version, tools will not accept arguments (execute "as is" with current environment variables). In the future, we can add parameter parsing from `{{variable}}`.
- **Security?**
    - The server runs on localhost. Access is open to local processes. This is standard for local MCP servers.
