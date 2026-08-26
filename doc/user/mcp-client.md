# MCP Client Guide

PyPost provides an interactive **MCP Client** workspace tab for **outbound** MCP: connect
to a remote MCP server over Streamable HTTP, discover its tools, and invoke them with
schema-guided forms or raw JSON. This is the opposite direction from
[MCP Tools for AI Agents](mcp-tools.md), where PyPost **exposes** saved requests to local
agents.

## Inbound vs outbound MCP

| Direction | What you do | Where in PyPost |
| --- | --- | --- |
| **Outbound** | PyPost calls a remote MCP server | **MCP Client** tab (`Ctrl+N` → **MCP Client**) |
| **Inbound** | An AI agent calls tools PyPost exposes | **MCP Tool** checkbox + **MCP Servers…** |

See [MCP Tools for AI Agents](mcp-tools.md) for inbound setup. This guide covers outbound
MCP Client usage only.

## Opening an MCP Client tab

1. **New blank tab:** Press `Ctrl+N` or click the tab-bar **+**, then choose **MCP Client**
   from the protocol picker. A draft tab titled **New MCP Client** opens with an empty URL
   field.
2. Closing the last tab shows the same protocol picker; cancel leaves an empty workspace.

Saved MCP Client profiles in Collections (when available) open from the sidebar like HTTP
requests and WebSocket profiles. Until collection persistence ships, use a blank MCP Client
tab for ad-hoc testing.

## Connect and discover tools

1. Enter the MCP server URL (Streamable HTTP), for example `http://127.0.0.1:1080/mcp`.
   Use `{{ variable }}` placeholders from the active environment.
2. Optionally add **Headers** (for example `Authorization: Bearer {{ token }}`). Hidden
   environment values are masked in the UI.
3. Click **Connect**. PyPost initializes the session and runs `list_tools`.
4. Discovered tools appear in the tool browser (name and description). Click a tool to
   select it for invoke.
5. Use **Refresh** to re-run `list_tools` on the active session, or **Disconnect** to
   close the session.

The connection state badge shows lifecycle state such as `DISCONNECTED`, `CONNECTING`, or
`CONNECTED`. Connect failures display an actionable error message in the tab.

## Invoke a tool

1. Select a tool in the browser after a successful Connect.
2. Fill the argument form generated from the tool's input schema, or switch to raw JSON when
   the schema is unknown or complex.
3. Click **Invoke**. The result pane shows structured output, errors, and elapsed time.
4. Hidden secrets remain masked in displayed headers and results.

Failed invoke keeps the session connected and preserves the tool list so you can retry.

## Environment variables

The active environment dropdown applies to the MCP Client URL and **Headers** table the same
way as HTTP requests. Resolve `{{ host }}`, `{{ token }}`, and other placeholders before
Connect or Invoke.

## Legacy HTTP method MCP

Older collections may still contain saved requests with `method: "MCP"`. Those items use a
legacy HTTP-editor path until migration completes. For new outbound MCP work, always prefer
**MCP Client** from the protocol picker — see [Working with Requests](requests.md).

## Related guides

- [Interface](interface.md) — MCP Client editor layout in the workspace
- [MCP Tools for AI Agents](mcp-tools.md) — inbound tool exposure for agents
- [MCP Integration (full reference)](../mcp_integration.md) — transport and envelope details
