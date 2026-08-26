# PyPost User Guide

PyPost is a desktop HTTP client for testing APIs and turning saved requests into tools for
local AI agents (MCP). You craft requests in a graphical editor, organize them in
collections, switch environments (dev/prod), and optionally expose selected requests to
agents such as Cursor — without writing an MCP server.

## What you can do

- Send HTTP requests (GET, POST, PUT, DELETE, PATCH, and more)
- Connect to WebSockets (`ws://`, `wss://`), stream messages, presets, and sequences
- Organize requests in collections, import shared ones, and open them in tabs
- Store hosts, tokens, and other values in environments; switch with one dropdown
- Use `{{ variables }}` and template functions in URL, headers, params, and body
- Run Python scripts after a response (for example, save an auth token)
- Browse request history and copy requests as cURL
- Connect to remote MCP servers from an **MCP Client** tab (list tools, invoke)
- Mark requests and WebSocket profiles as MCP tools and let a local AI agent call them
- Tune timeouts, retries, themes, encryption, and metrics ports in Settings; configure
  each MCP endpoint's host and port in **MCP Servers…**

## Guide contents

1. [Getting Started](getting-started.md) — install, run, first request
2. [Interface](interface.md) — main window layout
3. [Working with Requests](requests.md) — create, send, body, response search
4. [WebSocket](websocket.md) — connecting, composing, streaming, presets, and probes
5. [MCP Client](mcp-client.md) — outbound connect, list tools, invoke remote servers
6. [Collections](collections.md) — save, import, rename, delete, open in a new tab
7. [Environments](environments.md) — variables, hidden secrets, encryption
8. [Templating](templating.md) — `{{ var }}` and functions
9. [Post-Request Scripts](scripts.md) — automation after the response
10. [History and Copy cURL](history-and-curl.md)
11. [MCP Tools for AI Agents](mcp-tools.md) — inbound: expose requests to Cursor and others
12. [Settings](settings.md) — preferences and safety options
13. [Hotkeys](hotkeys.md)
14. [Common Workflows](workflows.md) — end-to-end recipes

## Related docs

- [Example collections and environments](../../examples/README.md) — importable fixtures
- [MCP Integration (full reference)](../mcp_integration.md)
- [Prometheus Monitoring](../prometheus_monitoring.md)
- [Developer documentation](../dev/README.md)
