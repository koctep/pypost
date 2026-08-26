# MCP Tools for AI Agents

PyPost supports MCP in two directions. This guide covers **inbound** MCP only — exposing
saved HTTP requests and WebSocket profiles as tools that a **local AI agent** can call.
For **outbound** MCP (PyPost connects to a remote server, lists tools, and invokes them),
use the [MCP Client Guide](mcp-client.md) instead.

## Inbound vs outbound

| Direction | User goal | Primary UI |
| --- | --- | --- |
| **Inbound** (this guide) | Agent calls saved items | **MCP Tool**, **MCP** tab, **MCP Servers…** |
| **Outbound** | PyPost calls a remote MCP server | **MCP Client** tab (`Ctrl+N` → **MCP Client**) |

Do not confuse:

- **MCP Servers…** / **MCP Server Tools…** — manage **inbound** endpoints PyPost hosts for
  agents.
- **MCP Client** tab — **outbound** client that calls upstream MCP servers over HTTP.

## Inbound overview

PyPost can expose saved HTTP requests as **MCP tools** for a local AI agent (Cursor,
Claude Desktop, and similar). You mark requests in the UI — you do not write an MCP
server by hand.

For transport details, JSON envelope schema, and troubleshooting tables, see the full
[MCP Integration](../mcp_integration.md) guide.

## Setup in four steps

### 1. Mark a request as a tool

1. Open a request you have already tested with **Send**.
2. Check **MCP Tool** next to the URL bar.
3. On the **MCP** tab, set a clear description and parameters.
4. **Actions → Save** (`Ctrl+S`).

### 2. Add agent inputs (optional)

Use placeholders for values the agent should supply:

```text
{{ mcp.request.user_id }}
```

Put them in URL, headers, params, or body. The parameters table syncs from these
placeholders. Environment variables (for example `{{ host }}` or `{{ token }}`) are
resolved from that endpoint's selected environment and are **not** listed as agent-visible
secrets.

### 3. Create and start an MCP endpoint

1. Select **MCP Servers…** in the top bar, then **Add…**.
2. Choose the collection that contains the requests the agent may use.
3. Choose the environment that supplies this endpoint's variables and hidden keys.
4. Choose a unique host and port, save the row, select it, and click **Start**.

The top bar shows aggregate server state. Use **MCP Servers…** to see the state,
collection, environment, tools, and activity for one endpoint.

Default URL for agents (Streamable HTTP):

```text
http://127.0.0.1:1080/mcp
```

Host and port are configured per MCP Servers row. Prefer `127.0.0.1` — binding `0.0.0.0`
exposes unauthenticated tool execution on the network.

### 4. Connect the agent

Example Cursor config (`.cursor/mcp.json` or MCP settings):

```json
{
  "mcpServers": {
    "pypost": {
      "url": "http://127.0.0.1:1080/mcp"
    }
  }
}
```

Use **Streamable HTTP** (not legacy SSE-only). Prefer `/mcp` over deprecated `/sse/`.

## Endpoint isolation

Each endpoint uses only its selected collection and selected environment. Switching the
top-bar environment does not change a running endpoint. Use **Edit…** in **MCP Servers…**
to change a row; choose a different unique port for a separate agent workflow.

## What the agent receives

Successful `call_tool` results are a **JSON envelope** in the text payload (`status`,
`error`, `body`, optional `logs`) — not the raw HTTP body alone. Agents should parse JSON
before reading the upstream response. See [MCP Integration](../mcp_integration.md).

## WebSocket probe tools

PyPost allows exposing saved WebSocket profiles as bounded MCP probe tools for AI agents:

1. Open a saved WebSocket profile, check **MCP Tool**, and configure its description on the
   **MCP** tab.
2. Configure bounded execution safeguards:
   - `max_duration_sec`: Maximum seconds to keep the socket open (default: 30s).
   - `max_messages`: Maximum number of frames to capture before auto-closing (default: 100).
   - `stop_when`: Optional regex string matching inbound frame payloads to stop early.
3. When called by an AI agent, PyPost connects in a background worker, runs initial message
   sequences if configured, captures incoming/outgoing frames within the bounds, and returns
   a structured JSON transcript.
4. Hidden environment secrets are masked in the transcript before delivery to the agent.

See [WebSocket Guide](websocket.md) for session details.

## In-app helpers

- **MCP Servers…** — add, edit, start, stop, remove, inspect tools, and inspect activity
  for each endpoint
- **MCP Server Tools…** — opens the server manager so tool inspection stays scoped to the
  selected endpoint

## Safety reminders

- Keep MCP on localhost unless you fully understand the risk
- Hidden env vars are used at execution time but not exposed in tool schemas
- Test each tool with **Send** in the GUI before relying on the agent

If you used the old environment-level **Enable MCP** option, open **MCP Servers…** and
select **Convert current legacy MCP setting…**. It copies the selected legacy environment
and legacy host/port into a new row; choose its collection and save before starting it.

Metrics for operators are separate: [Prometheus Monitoring](../prometheus_monitoring.md).
