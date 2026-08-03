# PyPost MCP Integration

See also [MCP Integration (Developer Guide)](dev/mcp_integration.md) for architecture,
implementation details, threading, and the structured tool-result schema.

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

2. **Create an endpoint**:
   - In the top bar, select **MCP Servers…**, then **Add…**.
   - Choose the collection whose MCP-enabled requests should be exposed and the
     environment whose variables should be used.
   - Choose a unique host/port (the default port is 1080) and save.
   - Select the row and click **Start**. The top bar shows the aggregate number
     of running MCP servers; the dialog shows each endpoint's exact state.

3. **Connect Agent**:
   - Use the **Streamable HTTP** MCP URL (current MCP spec). This is the recommended
     transport for new setups:

   ```
   http://127.0.0.1:1080/mcp
   ```

   `http://localhost:1080/mcp` is equivalent when PyPost listens on localhost.

   Replace host/port with the endpoint row you created. The observability MCP server (metrics
   resources) uses port **9080** by default: `http://127.0.0.1:9080/mcp`. See
   [Prometheus Monitoring](prometheus_monitoring.md) for the `/metrics` scrape endpoint.

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

After connecting, open Cursor chat with MCP enabled. The agent should **list tools** from
that endpoint's selected collection and **call tools** using that endpoint's selected
environment.

## Endpoint-specific collection and environment

Each MCP endpoint has its own selected collection and environment. Switching the top-bar
environment does not change a running endpoint's tool catalog or credentials. To change an
endpoint, open **MCP Servers…**, edit its row, and reconnect the agent if its host or port
changed. Ports must be unique across configured endpoints.

For an existing environment that still has **Enable MCP Server** selected, use **MCP
Servers… → Convert current legacy MCP setting…**. It preselects that environment and legacy
host/port, but you must choose a collection; conversion does not alter the legacy setting.

## Tool call responses (JSON envelope)

Every successful PyPost `call_tool` returns a **JSON envelope** in the MCP `TextContent.text`
field — not the raw upstream HTTP body. Agents and operators must parse it with `json.loads`
before reading outcomes.

| Field | Type | Meaning |
| --- | --- | --- |
| `status` | `int` | Upstream HTTP status; `0` when PyPost could not complete the request |
| `error` | `bool` | `true` when PyPost execution failed; `false` for completed HTTP calls (including 4xx/5xx) |
| `body` | `str` | Upstream response body (may be JSON text or plain text) |
| `logs` | `string[]` | Optional post-request script log lines |

Example (Python MCP client):

```python
import json

payload = json.loads(result.content[0].text)
if payload["error"]:
    raise RuntimeError(payload.get("error_message", "PyPost execution failed"))
http_status = payload["status"]
response_body = payload["body"]
script_logs = payload.get("logs", [])
```

**Breaking change:** Agents that treated tool output as raw HTTP body text must migrate to
JSON parsing. Protocol errors (unknown tool, internal server failure) are **not** JSON
envelopes — they remain plain text or MCP errors.

Full schema and error semantics:
[Developer MCP guide](dev/mcp_integration.md#structured-tool-results-pypost-557).

**Verify in Cursor:**

1. Confirm the MCP server shows as connected (no transport or handshake errors).
2. Ask the agent to list available PyPost MCP tools — names match requests marked "MCP Tool".
3. Invoke one tool (e.g. a simple GET) and confirm the agent parses the JSON envelope
   (`status`, `error`, `body`, optional `logs`) — not raw HTTP body text alone.
4. Optional: add a system prompt telling the agent to `json.loads` PyPost tool `TextContent`.

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

## Server settings

Host and port are configured per **MCP Servers…** row. Every configured row must have a
unique port. If a running-row edit cannot bind, PyPost retains the previous endpoint and
reports the error in that row; other endpoints remain available. Prefer `127.0.0.1` — binding
`0.0.0.0` makes unauthenticated tool execution available on the network.

## Troubleshooting

| Symptom | Likely cause | What to try |
| --- | --- | --- |
| Cursor shows disconnected / transport error | Wrong URL or type (SSE instead of Streamable HTTP) | Use `http://127.0.0.1:1080/mcp` and Streamable HTTP |
| No tools listed | Wrong endpoint collection or no requests marked MCP Tool | Open **MCP Servers… → Tools…** for that row; check the collection and "MCP Tool" on requests |
| Tool call fails | Missing env vars or bad request template | Define variables in the endpoint's selected environment; test send in GUI first |
| Agent misreads HTTP status | Treating `TextContent.text` as raw body | Parse JSON envelope; read `status` and `error` fields |
| Wrong host or credentials mid-session | Endpoint was edited or client uses the wrong URL | Verify the selected MCP Servers row and reconnect to its host/port |
| Connection refused | PyPost not running, row not started, or port unavailable | Start the selected MCP Servers row and inspect its row-specific error |

Automated `list_tools` / `call_tool` coverage lives in `tests/test_mcp_server_integration.py`.
