# MCP Reverse Proxy (Developer Guide)

This document describes the design, implementation, configuration, and troubleshooting of the **Model Context Protocol (MCP) Reverse Proxy** feature in PyPost (PYPOST-1092).

See also:
- [MCP Integration (Developer Guide)](mcp_integration.md) for local MCP collection server architecture.
- [Multiple Independent MCP Servers (PYPOST-1044)](mcp_server_registry.md) for multi-server lifecycle and registry management.
- [MCP Secrets Policy](mcp_secrets_policy.md) and [Sensitive Data Masking Policy](sensitive_data_masking_policy.md).
- [MCP Server Custom Headers Editor](mcp_server_headers_editor.md) for headers UI and variable autocomplete.
- [Inbound MCP Trust Model](mcp_trust_model.md).

---

## Overview

PyPost supports running in two distinct MCP server modes:
1. **Local Tool Server (`server_type="local"`)**: Exposes requests in a saved PyPost collection as callable MCP tools executed locally via `RequestService`.
2. **Reverse Proxy Server (`server_type="proxy"`)**: Acts as an MCP protocol reverse proxy. PyPost hosts local MCP endpoints (Streamable HTTP `/mcp` and legacy SSE `/sse`) and transparently forwards all standard MCP protocol operations (`list_tools`, `call_tool`, `list_prompts`, `get_prompt`, `list_resources`, `read_resource`, `list_resource_templates`) to a remote upstream MCP server.

### Key Capabilities
- **Protocol Bridging**: Inbound AI clients (Claude Desktop, Cursor, CLI agents) can connect over Streamable HTTP or SSE, while PyPost dispatches to the upstream server using its configured upstream transport.
- **Dynamic Header Templating**: Outgoing requests to upstream MCP servers support dynamic headers evaluated against PyPost environment variables using Jinja2 / `{{ VAR }}` placeholder syntax (e.g. `Authorization: Bearer {{ API_KEY }}`).
- **Fail-Fast Security**: If a header references an undefined environment variable, the proxy halts dispatch before sending network traffic, preventing leaking unauthenticated or placeholder-polluted requests.
- **End-to-End Secret Sanitization**: Sensitive header values (`Authorization`, `X-API-Key`, etc.) and values matching hidden environment variables are redacted in logs, telemetry, and activity viewer widgets.

---

## Architecture & Components

The MCP Proxy architecture consists of several cooperating layers bridging UI configuration, server lifecycle, header evaluation, protocol translation, and observability:

```
┌─────────────────────────────────────────────────────────────┐
│                   AI Client (Claude / Cursor)               │
└──────────────────────────────┬──────────────────────────────┘
                               │ MCP Protocol (HTTP / SSE)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 PyPost Application Process                  │
│                                                             │
│  ┌───────────────────────┐       ┌───────────────────────┐  │
│  │   MCPServerRegistry   │──────▶│   MCPServerManager    │  │
│  └───────────────────────┘       └───────────┬───────────┘  │
│                                              │ Spawns thread│
│                                              ▼              │
│                                  ┌───────────────────────┐  │
│                                  │  MCPProxyServerImpl   │  │
│                                  └───────────┬───────────┘  │
│                                              │              │
│       ┌──────────────────────────────────────┼──────────┐   │
│       ▼                                      ▼          ▼   │
│ ┌───────────────┐                  ┌─────────────┐ ┌──────┐ │
│ │ Proxy Headers │                  │ ActivityLog │ │Metric│ │
│ │ (resolve/mask)│                  │ & Sanitizer │ │System│ │
│ └───────┬───────┘                  └─────────────┘ └──────┘ │
│         ▼                                                   │
│ ┌───────────────┐                                           │
│ │TemplateService│                                           │
│ │& Active Env   │                                           │
│ └───────────────┘                                           │
└──────────────────────────────┬──────────────────────────────┘
                               │ Outgoing MCP Transport
                               │ (Streamable HTTP or SSE)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│            Remote / Upstream MCP Server Endpoint            │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

### 1. `MCPProxyServerImpl` (`pypost/core/mcp_proxy_server_impl.py`)
Encapsulates the Starlette web application and protocol forwarding logic:
- Hosts the Starlette application with routes for modern Streamable HTTP (`/mcp`) via `build_streamable_http_route` and legacy SSE (`/sse`) via `build_legacy_sse_app`.
- Registers protocol request handlers with the `mcp.server.Server` instance:
  - `list_tools()` -> connects upstream, calls `session.list_tools()`.
  - `call_tool(name, arguments)` -> connects upstream, calls `session.call_tool(name, arguments)`.
  - `list_prompts()` -> connects upstream, calls `session.list_prompts()`.
  - `get_prompt(name, arguments)` -> connects upstream, calls `session.get_prompt(name, arguments)`.
  - `list_resources()` -> connects upstream, calls `session.list_resources()`.
  - `read_resource(uri)` -> connects upstream, calls `session.read_resource(uri)`.
- Bridges dynamic environment variables via callable suppliers: `variable_supplier: Callable[[], dict[str, str]]` and `hidden_keys_supplier: Callable[[], set[str]]`.
- Manages upstream connection context managers (`_connect_upstream`) and maps transport errors into standard MCP protocol error payloads.
- Records structured telemetry events to `MetricsTrackerProtocol` and detailed activity records to `McpActivityLog`.

### 2. Header Resolution & Sanitization Engine (`pypost/core/mcp_proxy_headers.py`)
Provides deterministic header resolution and defense-in-depth secret masking:
- `resolve_proxy_headers(headers, env_vars, template_service)`:
  - Scans header values for `{{ VAR }}` template placeholders using `tokenize_template_expressions`.
  - Verifies that every referenced variable exists in `env_vars`. If any variable is missing, raises `McpUnresolvedVariableError(variable_name, header_name)`.
  - Renders values using `TemplateService.render_string` (or regex fallback), supporting filters and expressions.
- `sanitize_proxy_headers(headers, env_vars, hidden_keys)`:
  - Replaces sensitive header values (`Authorization`, `X-API-Key`, `Cookie`, `Proxy-Authorization`, `X-Auth-Token`) with masked tokens (e.g. `Bearer ***` or `***`).
  - Redacts occurrences of environment variables listed in `hidden_keys` using `sanitize_text`.

### 3. `MCPServerManager` (`pypost/core/qt/mcp_server.py`)
Extends background worker lifecycle management to proxy servers:
- `start_proxy_server(port, host, upstream_url, upstream_transport, headers, timeout, variable_supplier, hidden_keys_supplier, activity_log, metrics, template_service)`:
  - Instantiates `MCPProxyServerImpl`.
  - Starts Uvicorn in a dedicated worker `threading.Thread` running an asyncio event loop.
  - Emits Qt signals (`status_changed`, `start_failed`) to notify the UI when the server successfully binds or fails.
- Exposes `update_proxy_environment(env_vars, hidden_keys)` to update variable snapshots live without needing a server restart.

### 4. `MCPServerRegistry` (`pypost/core/mcp_server_registry.py`)
Coordinates persistence and multi-instance orchestration:
- Checks `config.server_type`:
  - For `"local"`, validates collection existence and starts local `MCPServerImpl`.
  - For `"proxy"`, skips collection checks, binds the active environment snapshot, and starts `MCPProxyServerImpl`.
- In `refresh_environment(environment_id, env_vars, hidden_keys)`, propagates updated variables to running proxy instances using `update_proxy_environment`.
- In `reconcile_references(collection_ids, environment_ids)`, preserves proxy configurations when collections are deleted.

---

## Upstream Transports

PyPost supports two upstream client transports configured via `upstream_transport`:

| Transport | Value | MCP Client Implementation | Description |
|---|---|---|---|
| **Streamable HTTP** | `"streamable_http"` | `mcp.client.streamable_http.streamable_http_client` | Default & recommended for modern MCP servers. Operates over standard HTTP with optional streaming. Uses `create_mcp_http_client(headers=...)`. |
| **Server-Sent Events** | `"sse"` | `mcp.client.sse.sse_client` | Legacy HTTP+SSE transport. Sends GET to establish event stream and POST to `/messages` endpoint. Passes resolved headers and `sse_read_timeout`. |

Inbound clients connecting to PyPost can use either Streamable HTTP (`/mcp`) or SSE (`/sse`) regardless of the upstream server's transport. PyPost acts as an asynchronous transport translator.

---

## Dynamic Header Resolution

### Template Syntax
Custom headers configured on a proxy server can contain template expressions resolved dynamically per request:
```
Authorization: Bearer {{ API_KEY }}
X-Custom-Tenant: {{ TENANT_ID }}
X-Trace-Id: {{ req_id | default('none') }}
```

### Fail-Fast Variable Semantics
Header evaluation executes *before* initiating any upstream network connection.
- If any template placeholder references an environment variable not present in the active environment snapshot, `resolve_proxy_headers` raises `McpUnresolvedVariableError`.
- `MCPProxyServerImpl` catches this exception, logs a warning with the missing variable name, records an error entry in `McpActivityLog`, and returns an informative MCP error response:
  ```json
  {
    "error": {
      "code": -32603,
      "message": "MCP Proxy header resolution failed: Missing environment variable: 'API_KEY' in header 'Authorization'"
    }
  }
  ```
- **Security guarantee**: Outgoing HTTP requests are never sent upstream with unresolved template tags like `Bearer {{ API_KEY }}`.

---

## Secrets Masking & Sanitization

To prevent credential leakage across application boundaries:
1. **Activity Logs (`McpActivityLog`)**:
   - `McpActivityEntry.headers` records only sanitized header representations via `sanitize_proxy_headers`.
   - `Authorization: Bearer my-secret-token` is stored as `Authorization: Bearer ***`.
   - Any sensitive header key listed in `_SENSITIVE_HEADER_NAMES` has its value replaced with `***`.
   - Environment values configured with `hidden=True` are scrubbed from log details.
2. **Structured Application Logs (`logging`)**:
   - Upstream connection diagnostics log only the list of header keys (`header_keys=['Authorization', 'X-Tenant']`), never raw values.
3. **UI Display (`McpActivityDialog`, `McpServersDialog`)**:
   - Table views and detail inspectors display masked values.

---

## Configuration & UI Editor

### `McpServerConfiguration` Data Model (`pypost/models/settings.py`)

| Field | Type | Default | Description |
|---|---|---|---|
| `id` | `str` | `uuid4()` | Unique server instance identifier. |
| `name` | `str` | `""` | User-defined label (e.g. `"Atlassian Jira Gateway"`). |
| `server_type` | `Literal["local", "proxy"]` | `"local"` | `"local"` for collection tools, `"proxy"` for remote upstream proxy. |
| `host` | `str` | `"127.0.0.1"` | Host address for PyPost's local listener. |
| `port` | `int` | `8000` | Port for PyPost's local listener (1–65535). |
| `upstream_url` | `Optional[str]` | `None` | Target MCP server URL (required when `server_type="proxy"`). |
| `upstream_transport` | `Literal["streamable_http", "sse"]` | `"streamable_http"` | Upstream transport protocol. |
| `headers` | `dict[str, str]` | `{}` | Custom HTTP headers sent to upstream. Supports `{{ VAR }}`. |
| `timeout` | `float` | `30.0` | Upstream request timeout in seconds (> 0). |
| `collection_id` | `Optional[str]` | `None` | Collection ID (required when `server_type="local"`). |
| `environment_id` | `Optional[str]` | `None` | Environment snapshot for variable resolution. |
| `enabled` | `bool` | `True` | Whether server starts automatically. |

### UI Editor (`pypost/ui/dialogs/mcp_servers_dialog.py`)
In the **MCP Servers** settings dialog (`McpServersDialog`), the editor dynamically adjusts based on the selected **Server Type**:
- **Local Collection Server**: Displays Collection dropdown and Environment dropdown.
- **Upstream Proxy**:
  - Displays **Upstream URL** line edit with validation (must begin with `http://` or `https://`).
  - Displays **Upstream Transport** dropdown (`Streamable HTTP`, `Server-Sent Events (SSE)`).
  - Displays **Custom Headers** key-value table allowing addition, modification, and deletion of custom headers with `{{ VAR }}` autocompletion.
  - Hides Collection dropdown; keeps Environment dropdown for variable resolution.
  - Shows target endpoint in the servers table (`[Proxy] https://api.example.com/mcp` vs `[Local] Collection Name`).

---

## Troubleshooting & Error Handling

### Error Mapping Reference

| Failure Condition | Exception Raised | Proxy Log Event | Client MCP Response |
|---|---|---|---|
| Missing template variable | `McpUnresolvedVariableError` | `mcp_proxy_unresolved_variable` | Protocol Error: `Missing environment variable: '<var>' in header '<header>'` |
| Upstream unreachable | `httpx.ConnectError`, `httpx.NetworkError` | `mcp_proxy_upstream_connect_error` | Protocol Error: `Failed to connect to upstream MCP server (<url>): <reason>` |
| Upstream timeout | `httpx.TimeoutException`, `TimeoutError` | `mcp_proxy_upstream_timeout` | Protocol Error: `Upstream MCP server timed out after <timeout>s` |
| Upstream HTTP 4xx/5xx | `httpx.HTTPStatusError` | `mcp_proxy_upstream_http_error` | Protocol Error: `Upstream MCP server returned HTTP <status>` |
| Upstream internal error | `Exception` | `mcp_proxy_forward_error` | Protocol Error: `Upstream MCP error: <message>` |

### Common Issues and Solutions

1. **"Missing environment variable: 'TOKEN' in header 'Authorization'"**:
   - *Cause*: The proxy server configuration has an associated environment that does not define `TOKEN`, or no environment is selected.
   - *Fix*: Select the appropriate environment in the server configuration editor or add the missing variable to the active environment in the Environments dialog.

2. **"Failed to connect to upstream MCP server (http://localhost:9000/mcp): Connection refused"**:
   - *Cause*: The remote MCP server is not running or unreachable on the specified host/port.
   - *Fix*: Verify the upstream server is running and accessible from the machine running PyPost.

3. **Port collision on local bind**:
   - *Cause*: Another process or MCP server instance is already listening on the configured local port.
   - *Fix*: Change the local port in the MCP Servers dialog to an unused port number (e.g. 8001).

4. **Upstream MCP server returned 401 Unauthorized**:
   - *Cause*: The resolved headers do not contain valid credentials accepted by the upstream server.
   - *Fix*: Check the resolved variable value in the environment editor and verify header format (e.g. ensure `Bearer ` prefix is included if required by the upstream server).
