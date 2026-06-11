# MCP Integration (Developer Guide)

This document describes the internal implementation of the **Model Context Protocol (MCP)** server within PyPost.

## Overview

PyPost implements an **MCP Server** using the official Python SDK (`mcp`). This allows external MCP Clients (like Claude Desktop or Cursor) to connect to PyPost and execute HTTP requests defined in the user's collections as "Tools".

## Architecture

The integration is split into two main layers to bridge the synchronous Qt world and the asynchronous ASGI/Starlette world.

### 1. `MCPServerManager` (`pypost/core/mcp_server.py`)

This class acts as the bridge between the PySide6 UI and the background MCP server.

*   **Responsibility**: Lifecycle management (Start/Stop/Restart).
*   **Threading**: It spawns a dedicated `threading.Thread` to run the `uvicorn` server. This is necessary because `uvicorn` blocks the thread it runs in, and we cannot block the main Qt GUI thread.
*   **Configuration**: Supports configurable `host` and `port` via `start_server`.
*   **Communication**: Uses Qt Signals (`status_changed`) to notify the UI about server state.
*   **Shutdown**: Handles the complex logic of stopping `uvicorn` from another thread by setting flags and waiting for the thread to join.

### 2. `MCPServerImpl` (`pypost/core/mcp_server_impl.py`)

This class contains the actual business logic of the MCP server.

*   **Framework**: Uses `Starlette` + `mcp` SDK + `uvicorn`.
*   **Transport**: **Streamable HTTP** (current MCP spec) at `GET/POST /mcp`, with optional
    legacy **SSE** under `/sse` for backward-compatible clients.
    *   Primary: `http://<host>:<port>/mcp` — Streamable HTTP session (POST initialize,
      optional GET SSE stream for server messages).
    *   Legacy: GET `/sse/` + POST `/sse/messages` — deprecated HTTP+SSE transport.
*   **Tool Registration**: Converts `RequestData` objects (where `expose_as_mcp=True`) into MCP `Tool` definitions.
*   **Schema Generation**: Automatically generates JSON Schema for tools by parsing the request URL, headers, and body using `TemplateService` (Jinja2 AST) to find variables matching the pattern `{{ mcp.request.VAR_NAME }}`.
*   **Execution**: Delegates request execution to `RequestService`.
*   **Environment variables (PYPOST-550)**: At `call_tool` time, snapshots active
    environment variables via an injected `variable_supplier`, merges them with MCP tool
    arguments, and passes the combined dict to `RequestService.execute()` (GUI parity).

### 3. `EnvPresenter` (`pypost/ui/presenters/env_presenter.py`)

The environment selector owns MCP lifecycle and the active-variable cache used by MCP tools.

*   **Responsibility**: Load environments, emit variable changes to the UI, start/stop MCP
    when `enable_mcp` is set on the selected environment.
*   **Variable cache**: `_current_variables` is updated on the main thread in
    `_on_env_changed` whenever the user selects or edits an environment.
*   **Supplier registration**: On init, calls
    `MCPServerManager.set_variable_supplier(lambda: dict(self._current_variables))`.
    The lambda returns a **copy** so MCP threadpool workers never observe partial writes.

### 4. `MetricsManager` (`pypost/core/metrics.py`)

PyPost also exposes a separate MCP server dedicated to observability.

*   **Role**: Provides application metrics via MCP Resources.
*   **Framework**: Same stack as the main server (`Starlette` + `mcp` SDK + `uvicorn`).
*   **Hybrid Server**: Hosts Prometheus (`/metrics`), Streamable HTTP MCP (`/mcp`), and
    legacy SSE (`/sse`, `/messages`) on the same port (default 9080).
*   **Resources**:
    *   `metrics://all`: Returns the full Prometheus metrics dump as `text/plain`.

## Key Flows

### Server Startup

1.  User selects an Environment with `enable_mcp=True`.
2.  `MainWindow` calls `MCPServerManager.start_server(port, tools, host)`.
3.  `MCPServerManager` creates a new thread.
4.  Inside the thread, a new `asyncio` event loop is created.
5.  `MCPServerImpl.create_app()` builds the Starlette app.
6.  `uvicorn.Server.serve()` is called to start listening on the specified host and port.

### Tool Execution

1.  External Client sends a `call_tool` request via Streamable HTTP (`/mcp`).
2.  `MCPServerImpl.call_tool` is invoked (async).
3.  **Context Switching**: Since `RequestService` is synchronous, execution is offloaded to a thread pool using `starlette.concurrency.run_in_threadpool`.
4.  `_execute_request_sync` builds the variables dict:
    -   Calls `variable_supplier()` for a snapshot of the active environment's flat keys
        (e.g. `base_url`, `api_key`).
    -   Merges with MCP tool arguments via `_merge_execution_variables` (see below).
5.  `RequestService.execute()` is called with the merged dict.
    -   It renders templates (environment placeholders **and** `{{ mcp.request.* }}`).
    -   Executes the HTTP request via `HTTPClient`.
    -   Runs any post-request scripts via `ScriptExecutor` (same variable dict as GUI).
6.  Response body (plus any script logs/errors) is returned as `TextContent` to the MCP Client.

### Environment variable injection (PYPOST-550)

MCP tool calls must resolve the same `{{ variable }}` placeholders as GUI sends. The fix
lives entirely in the MCP adapter — `RequestService`, `TemplateService`, and `HTTPClient` are
unchanged.

#### Variable dict shape

`TemplateService` renders against a single Jinja2 context:

| Placeholder | Dict path | Source |
| --- | --- | --- |
| `{{ base_url }}` | top-level key | Active environment |
| `{{ mcp.request.user_id }}` | `mcp.request.user_id` | Agent `call_tool` arguments |

Merge contract (module-level helper in `mcp_server_impl.py`):

```python
def _merge_execution_variables(env_vars, mcp_args):
    return {**env_vars, "mcp": {"request": mcp_args}}
```

The `mcp` namespace **always wins**: an environment variable named `mcp` cannot override
`mcp.request.*` tool arguments.

#### Wiring

```
EnvPresenter._current_variables  (main thread, updated in _on_env_changed)
        │
        ▼  set_variable_supplier(λ: dict(_current_variables))
MCPServerManager ──► MCPServerImpl._variable_supplier
        │
        ▼  per call_tool (threadpool worker)
_build_execution_variables(mcp_args) ──► RequestService.execute(request, merged)
```

Freshness: the supplier is invoked on **every** `call_tool`, so edits to environment
variables take effect on the next agent call without restarting MCP (existing restart-on-env
change behavior is unchanged).

#### GUI parity

| Path | Variables passed to `RequestService.execute()` |
| --- | --- |
| GUI (`RequestWorker`) | Flat env dict from `TabsPresenter._current_variables` |
| MCP (`MCPServerImpl`) | Merged env dict + `mcp.request` namespace |

Hidden variables: masking applies to UI/history only. MCP execution uses real stored values,
consistent with GUI sends. MCP inbound tools do not record history, so `hidden_keys` is not
wired on this path.

#### Observability

DEBUG log in `_build_execution_variables`: `mcp_execution_variables_merged` with
`env_var_count` and `mcp_arg_count` (no names or values). See
`ai-tasks/PYPOST-550/50-observability.md`.

## Threading Model

*   **Main Thread (Qt)**: UI, Dialogs, Settings.
*   **Worker Thread (`RequestWorker`)**: Used for GUI-initiated requests.
*   **MCP Thread (`MCPServerManager`)**: Runs the `uvicorn` loop.
    *   **Thread Pool**: Used inside MCP Thread for blocking I/O (Request execution).
    *   **Variable supplier**: Must not call Qt APIs. `EnvPresenter` reads only
        `_current_variables` (main-thread cache); supplier returns `dict(...)` snapshot.
*   **Metrics Thread (`MetricsManager`)**: Runs its own isolated `uvicorn` loop for metrics and observability.

## API / Usage

### `MCPServerManager.set_variable_supplier(supplier)`

Register a callable that returns the current active environment variables as `dict[str, str]`.
Called by `EnvPresenter` at init. Forwarded to `MCPServerImpl`. Pass `None` to reset to an
empty dict.

### `MCPServerImpl._build_execution_variables(mcp_args)`

Internal. Invokes `_variable_supplier()`, logs merge counts at DEBUG, returns merged dict for
`RequestService.execute()`.

### `_merge_execution_variables(env_vars, mcp_args)`

Pure merge helper; unit-tested independently. Spread env vars first, then set `"mcp"` from tool
arguments.

## Configuration

No new settings. MCP tools use variables from the **currently selected environment** when
`enable_mcp=True`. Port and host remain in `AppSettings` (`mcp_port`, `mcp_host`).

### Agent connection URL

Configure local MCP clients (Cursor, Claude Desktop, etc.) with Streamable HTTP:

| Server | Default port | URL |
| --- | --- | --- |
| Request tools | 1080 | `http://127.0.0.1:1080/mcp` |
| Metrics / observability | 9080 | `http://127.0.0.1:9080/mcp` |

Legacy SSE clients may use `http://127.0.0.1:<port>/sse/` until reconfigured.

## Troubleshooting

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| MCP tool URL still has `{{ base_url }}` unresolved | No environment selected, or supplier not registered | Select an environment with the variable defined; verify `EnvPresenter` wired the supplier |
| Stale env values after editing variables | Supplier not invoked or cache not updated | `_on_env_changed` must refresh `_current_variables`; supplier runs per `call_tool` |
| `{{ mcp.request.x }}` works but env vars do not | Custom MCP setup without supplier | Call `set_variable_supplier` before `start_server`, or use default `EnvPresenter` wiring |
| Env var named `mcp` ignored for nested keys | By design — merge preserves `mcp.request.*` | Rename the environment variable |
| DEBUG shows `env_var_count=0` | "No Environment" selected or empty env | Expected when no env is active; only MCP args resolve |

## Limitations & Tech Debt

*   **Synchronous Execution**: The core uses `requests` (sync). Ideally, we should move to `httpx` for async support to avoid `run_in_threadpool`.
*   **Parsing**: Schema generation uses `TemplateService` for AST parsing, but complex Jinja2 constructs might still need attention.
*   **Schema vs execution**: `list_tools` JSON Schema still exposes only `mcp.request.*` placeholders; environment variables are resolved at execution time and are not listed as tool inputs.
*   **Dual variable sources in EnvPresenter**: `current_variables` property reads the combo box while MCP uses `_current_variables` cache (see `ai-tasks/PYPOST-550/60-tech-debt.md`).

See `ai-tasks/PYPOST-20/40-tech-debt.md` for more details.
