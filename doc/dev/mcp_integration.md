# MCP Integration Developer Guide

This document describes the technical details of Model Context Protocol (MCP) integration in PyPost.

## Overview

PyPost acts as an MCP Server, exposing saved requests as tools. This allows AI agents to execute HTTP requests defined in PyPost.

## Architecture

- **`pypost.core.mcp_server.MCPServerManager`**: Manages the server thread and lifecycle.
- **`pypost.core.mcp_server_impl.MCPServerImpl`**: Implements the MCP protocol logic (list_tools, call_tool) using `mcp` SDK and `starlette` for SSE transport.
- **Transport**: SSE (Server-Sent Events).
- **Port**: Default 8000 (configurable).

## Key Components

### MCPServerImpl

Uses `mcp.server.Server` to handle protocol messages.
Runs a `Starlette` app to serve SSE endpoints (`/sse`, `/messages`).

### Tool Exposure

Requests are converted to tools if `expose_as_mcp` is True.
- **Tool Name**: Sanitized request name (alphanumeric + underscores).
- **Tool Description**: "Execute request: {request.name}".
- **Arguments**: Currently no arguments are supported (empty schema).

## Running the Server

The server is started automatically if `enable_mcp` is set to True in the active environment.
It runs in a separate `QThread` to avoid blocking the main Qt event loop.

## Debugging

You can use the [MCP Inspector](https://github.com/modelcontextprotocol/inspector) to debug the server.
Command:
```bash
npx @modelcontextprotocol/inspector http://localhost:8000/sse
```
