# MCP Tools for AI Agents

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
placeholders. Environment variables (for example `{{ host }}` or `{{ token }}`) stay
resolved from the active environment and are **not** listed as agent-visible secrets.

### 3. Enable the MCP server on an environment

1. Open **Manage Environments** (`Ctrl+E`).
2. Select the environment the agent should use.
3. Check **Enable MCP (Model Context Protocol)**.
4. Save. The top bar should show **MCP: ON** with the configured host and port.

Default URL for agents (Streamable HTTP):

```text
http://127.0.0.1:1080/mcp
```

Host and port are configurable in **Settings**. Prefer `127.0.0.1` — binding `0.0.0.0`
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

## Active environment

Tool calls always use the environment selected in PyPost's top bar. Switching environments
mid-session changes hosts and credentials without notifying the agent.

## What the agent receives

Successful `call_tool` results are a **JSON envelope** in the text payload (`status`,
`error`, `body`, optional `logs`) — not the raw HTTP body alone. Agents should parse JSON
before reading the upstream response. See [MCP Integration](../mcp_integration.md).

## In-app helpers

- **MCP Tools** — list of exposed tools for the active environment
- **MCP Activity** — recent `list_tools` / `call_tool` events

## Safety reminders

- Keep MCP on localhost unless you fully understand the risk
- Hidden env vars are used at execution time but not exposed in tool schemas
- Test each tool with **Send** in the GUI before relying on the agent

Metrics for operators are separate: [Prometheus Monitoring](../prometheus_monitoring.md).
