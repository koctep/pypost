# Interface

The main window is divided into these areas:

## Overview layout

```text
+---------------------------------------------------------------------------------------+
| Menu Bar: File | Help                                                                 |
+---------------------------------------------------------------------------------------+
| Environment: [Local v] [Manage Ctrl+E] | MCP: [Servers...] Status: 1 running          |
+-----------------------+---------------------------------------------------------------+
| SIDEBAR (Left)        | WORKSPACE (Right) - Tabs: [Request 1 (GET)] [+]               |
| [Collections][History]|---------------------------------------------------------------|
|                       | [GET  v] [ https://httpbin.org/get          ] [Send F5] [Actions]|
| v My Collection       |---------------------------------------------------------------|
|   - List Items        | Tabs: [Params] [Headers] [Body] [Script] [MCP]                |
|   - Create Item       | Key-value parameters, headers, JSON body editor, scripts      |
|                       |---------------------------------------------------------------|
|                       | RESPONSE PANE                                                 |
|                       | Status: 200 OK | Time: 120ms | Size: 1.1 KB | Search (Ctrl+F) |
|                       | { "args": {}, "headers": { ... }, "origin": "..." }           |
+-----------------------+---------------------------------------------------------------+
```

## Menu bar

- **File → Quit** (`Ctrl+Q`) — exit the application
- **Help → Hotkeys** — list of keyboard shortcuts
- **Help → About** — application information

## Environment panel (top bar)

- **Environment dropdown** — selects the active environment used for GUI request variable
  substitution; it does not retarget a configured MCP endpoint
- **Manage** (`Ctrl+E`) — open the environment manager
- **MCP Servers…** — create and manage independent endpoints, each with its own collection,
  environment, host, port, status, tools, and activity
- **MCP status** — aggregate running/failed server count; open **MCP Servers…** for a
  row's endpoint and error details
- **MCP Server Tools…** — opens the manager so tools are inspected for one selected server

## Sidebar (left)

- **Collections** — tree of collections and saved requests
- **History** — log of executed requests

Right-click items in the collections tree for actions such as open in a new tab, rename,
or delete.

## Workspace (right)

Tabs with HTTP request, WebSocket, and MCP Client editors. Each tab holds one draft or saved
profile: HTTP method/URL/body, an active WebSocket session, or an outbound MCP Client
connection (URL, headers, tool browser, invoke form).

- Click **+** or press `Ctrl+N` to open the **protocol picker** and choose **HTTP Request**,
  **WebSocket**, or **MCP Client** before a new tab is created
- Closing the last tab shows the same protocol picker (cancel leaves an empty workspace)
- Close with `Ctrl+W`
- Switch tabs with `Ctrl+Tab` / `Ctrl+Shift+Tab`, or `Alt+1` … `Alt+9`

## Request editor

From top to bottom in a typical layout:

1. Method combo, URL field, **Send**, **Actions** menu
2. Tabs: **Params**, **Headers**, **Body**, **Script**, and **MCP** (when relevant)
3. Response pane: status, time, size, body, and search (`Ctrl+F`)

**Actions** includes **Save As...**, **Save**, and **Copy cURL**.

## WebSocket editor

For WebSocket tabs, the layout provides a bi-directional session manager:

1. Connection bar: Target URL (`ws://` / `wss://`), **Connect** / **Disconnect** button, and
   connection state badge (`DISCONNECTED`, `CONNECTING`, `CONNECTED`, etc.).
2. Handshake configuration tabs: **Params** (query parameters), **Headers** (custom handshake
   headers), and **Subprotocols** (negotiated subprotocols).
3. Split workspace:
   - **Stream Inspector** (top): Live log of inbound and outbound frames with direction/kind
     filtering, search, auto-scroll tailing, payload inspection, and export (JSON, NDJSON, CSV).
   - **Composer & Messages** (bottom): Multi-format payload editor (Text, JSON, Binary),
     **Send Message** button, saved message presets, and automated test sequences.

See [WebSocket Guide](websocket.md) for full details.

## MCP Client editor

For **MCP Client** tabs (outbound MCP — PyPost calls a remote server), the layout provides
connect → discover → invoke workflow:

1. Connection bar: Target URL (Streamable HTTP, for example `http://127.0.0.1:1080/mcp`),
   **Connect** / **Disconnect** / **Refresh**, and connection state badge.
2. **Headers** table: Outbound request headers with `{{ variable }}` templating (for example
   `Authorization`).
3. Split workspace:
   - **Tool browser** (left): Remote tools from `list_tools` after Connect; click to select.
   - **Invoke column** (right): Schema-guided argument form or raw JSON editor, **Invoke**
     button, and structured result pane with elapsed time.

See [MCP Client Guide](mcp-client.md) for full details.

This editor is separate from **inbound** MCP surfaces: the **MCP Tool** checkbox and **MCP**
sub-tab on HTTP requests expose tools to agents; **MCP Servers…** runs local endpoints for
agents. See [MCP Tools for AI Agents](mcp-tools.md).

## Settings

Open with `Ctrl+,` or `F12`. See [Settings](settings.md).

