# MCP Integration (Developer Guide)

This document describes the internal implementation of the **Model Context Protocol (MCP)** server within PyPost.

## Overview

PyPost implements an **MCP Server** using the official Python SDK (`mcp`). This allows external MCP Clients (like Claude Desktop or Cursor) to connect to PyPost and execute HTTP requests defined in the user's collections as "Tools".

## Architecture

The integration is split into two main layers to bridge the synchronous Qt world and the asynchronous ASGI/Starlette world.

### 1. `MCPServerManager` (`pypost/core/mcp_server.py`)

This class acts as the bridge between the PySide6 UI and the background MCP server.

*   **Responsibility**: Lifecycle management (Start/Stop/Restart).
*   **Threading**: It spawns a dedicated `threading.Thread` to run the `uvicorn` server. This is necessary because `uvicorn` blocks the thread it runs in, and we cannot block the main Qt GUI thread.
*   **Configuration**: Supports configurable `host` and `port` via `start_server`.
*   **Communication**: Uses Qt Signals (`status_changed`) to notify the UI about server state.
*   **Shutdown**: Handles the complex logic of stopping `uvicorn` from another thread by setting flags and waiting for the thread to join.

### 2. `MCPServerImpl` (`pypost/core/mcp_server_impl.py`)

This class contains the actual business logic of the MCP server.

*   **Framework**: Uses `Starlette` + `mcp` SDK + `uvicorn`.
*   **Transport**: Implements **SSE (Server-Sent Events)** over HTTP.
    *   GET `/sse`: Establishes the connection.
    *   POST `/messages`: Receives client messages.
*   **Tool Registration**: Converts `RequestData` objects (where `expose_as_mcp=True`) into MCP `Tool` definitions.
*   **Schema Generation**: Automatically generates JSON Schema for tools by parsing the request URL, headers, and body using `TemplateService` (Jinja2 AST) to find variables matching the pattern `{{ mcp.request.VAR_NAME }}`.
*   **Execution**: Delegates request execution to `RequestService`.

### 3. `MetricsManager` (`pypost/core/metrics.py`)

PyPost also exposes a separate MCP server dedicated to observability.

*   **Role**: Provides application metrics via MCP Resources.
*   **Framework**: Same stack as the main server (`Starlette` + `mcp` SDK + `uvicorn`).
*   **Hybrid Server**: Hosts both the Prometheus metrics endpoint (`/metrics`) and the MCP SSE endpoints (`/sse`, `/messages`) on the same port (default 9091).
*   **Resources**:
    *   `metrics://all`: Returns the full Prometheus metrics dump as `text/plain`.

## Key Flows

### Server Startup

1.  User selects an Environment with `enable_mcp=True`.
2.  `MainWindow` calls `MCPServerManager.start_server(port, tools, host)`.
3.  `MCPServerManager` creates a new thread.
4.  Inside the thread, a new `asyncio` event loop is created.
5.  `MCPServerImpl.create_app()` builds the Starlette app.
6.  `uvicorn.Server.serve()` is called to start listening on the specified host and port.

### Tool Execution

1.  External Client sends a `call_tool` request via SSE/HTTP.
2.  `MCPServerImpl.call_tool` is invoked (async).
3.  **Context Switching**: Since `RequestService` is synchronous, execution is offloaded to a thread pool using `starlette.concurrency.run_in_threadpool`.
4.  `RequestService.execute()` is called.
    -   It renders templates.
    -   Executes the HTTP request via `HTTPClient`.
    -   Runs any post-request scripts via `ScriptExecutor`.
5.  Response body (plus any script logs/errors) is returned as `TextContent` to the MCP Client.

## Threading Model

*   **Main Thread (Qt)**: UI, Dialogs, Settings.
*   **Worker Thread (`RequestWorker`)**: Used for GUI-initiated requests.
*   **MCP Thread (`MCPServerManager`)**: Runs the `uvicorn` loop.
    *   **Thread Pool**: Used inside MCP Thread for blocking I/O (Request execution).
*   **Metrics Thread (`MetricsManager`)**: Runs its own isolated `uvicorn` loop for metrics and observability.

## Limitations & Tech Debt

*   **Synchronous Execution**: The core uses `requests` (sync). Ideally, we should move to `httpx` for async support to avoid `run_in_threadpool`.
*   **Parsing**: Schema generation uses `TemplateService` for AST parsing, but complex Jinja2 constructs might still need attention.

See `ai-tasks/PYPOST-20/40-tech-debt.md` for more details.
