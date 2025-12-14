# PyPost MCP Integration

PyPost supports the **Model Context Protocol (MCP)**, allowing it to act as a server for AI agents (like Claude Desktop, Cursor, etc.).

## What is it?

You can expose your saved HTTP requests as "tools" for AI. The AI agent can then execute these requests directly from the chat interface.

## How to use

1.  **Configure Request**:
    -   Open a request in PyPost.
    -   Check the **"MCP Tool"** checkbox (next to the URL bar).
    -   Save the request.

2.  **Enable Server**:
    -   Go to **Manage Environments**.
    -   Select your environment.
    -   Check **"Enable MCP Server"**.
    -   (Optional) Change port (default 8000).
    -   Click **Save**.
    -   You should see "MCP: ON" in the top bar.

3.  **Connect Agent**:
    -   In your AI agent configuration (e.g., `claude_desktop_config.json`), add PyPost as an MCP server:

    ```json
    {
      "mcpServers": {
        "pypost": {
          "command": "python", // Or path to python in venv
          "args": ["-m", "pypost.main"], // NOTE: PyPost currently runs as SSE server, not stdio
          // For SSE support, use the URL:
          "url": "http://localhost:8000/sse"
        }
      }
    }
    ```
    *Note: Client support for SSE varies. Check your agent's documentation.*

### Cursor

In Cursor settings (Features > MCP):
1. Add a new server.
2. Type: **SSE**.
3. URL: `http://localhost:1080/sse`.

Now you can use `@MCP` in Cursor chat and see your requests from PyPost.

## Server Settings

You can change MCP server settings in global settings (**Settings**):
- **MCP Server Port**: default `1080`.
- **MCP Server Host**: default `127.0.0.1`. Change to `0.0.0.0` to make the server available from external network.

If the port is busy or host is unavailable, the server will not start (check console/logs for errors).
