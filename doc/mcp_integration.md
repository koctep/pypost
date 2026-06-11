# PyPost MCP Integration

PyPost supports the **Model Context Protocol (MCP)**, allowing it to act as a server for AI
agents (like Cursor, Claude Desktop, etc.).

## What is it?

You can expose your saved HTTP requests as "tools" for AI. The AI agent can then execute
these requests directly from the chat interface.

## How to use

1. **Configure Request**:
   - Open a request in PyPost.
   - Check the **"MCP Tool"** checkbox (next to the URL bar).
   - Open **Actions** (right of **Send**) and click **Save** (or press `Ctrl+S`).

2. **Enable Server**:
   - Go to **Manage Environments**.
   - Select your environment.
   - Check **"Enable MCP Server"**.
   - (Optional) Change port (default 1080) or host in **Settings**.
   - Click **Save**.
   - You should see "MCP: ON" in the top bar.

3. **Connect Agent**:
   - Use the **Streamable HTTP** MCP URL (current MCP spec):

   ```
   http://127.0.0.1:1080/mcp
   ```

   Replace host/port if you changed MCP settings. The observability MCP server (metrics
   resources) uses port **9080** by default: `http://127.0.0.1:9080/mcp`.

### Cursor

Add PyPost in Cursor MCP settings (or project `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "pypost": {
      "url": "http://127.0.0.1:1080/mcp"
    }
  }
}
```

In the Cursor UI (**Settings → Features → MCP**):

1. Add a new server.
2. Type: **Streamable HTTP** (or remote URL, depending on Cursor version).
3. URL: `http://127.0.0.1:1080/mcp`.

After connecting, open Cursor chat with MCP enabled. The agent should **list tools** exposed
from your active PyPost environment and **call tools** on your behalf.

**Verify in Cursor:**

1. Confirm the MCP server shows as connected (no transport or handshake errors).
2. Ask the agent to list available PyPost MCP tools — names match requests marked "MCP Tool".
3. Invoke one tool (e.g. a simple GET) and confirm the response body appears in chat.

See [Cursor verification checklist](../ai-tasks/PYPOST-552/cursor-verification-checklist.md)
for a full manual checklist.

### Claude Desktop and other clients

Configure a remote MCP server with Streamable HTTP transport and the same URL. Client UI
labels vary; look for "URL", "Streamable HTTP", or "HTTP" — not legacy SSE-only modes.

Example (shape may differ by client version):

```json
{
  "mcpServers": {
    "pypost": {
      "url": "http://127.0.0.1:1080/mcp"
    }
  }
}
```

### Legacy SSE (optional)

PyPost still mounts deprecated HTTP+SSE endpoints at `/sse/` for older clients during the
ecosystem transition. New setups should use `/mcp`. Legacy URL example:

```
http://127.0.0.1:1080/sse/
```

## Server Settings

You can change MCP server settings in global settings (**Settings**):

- **MCP Server Port**: default `1080`.
- **MCP Server Host**: default `127.0.0.1`. Change to `0.0.0.0` to make the server available
  from external network.

If the port is busy or host is unavailable, the server will not start (check console/logs for
errors).

## Troubleshooting

| Symptom | Likely cause | What to try |
| --- | --- | --- |
| Cursor shows disconnected / transport error | Wrong URL or type (SSE instead of Streamable HTTP) | Use `http://127.0.0.1:1080/mcp` and Streamable HTTP |
| No tools listed | MCP off, wrong environment, or no requests marked MCP Tool | Enable MCP on environment; check "MCP Tool" on requests |
| Tool call fails | Missing env vars or bad request template | Define variables in active environment; test send in GUI first |
| Connection refused | PyPost not running or MCP not started | Select environment with MCP enabled; check "MCP: ON" in top bar |

Automated `list_tools` / `call_tool` coverage lives in `tests/test_mcp_server_integration.py`.
