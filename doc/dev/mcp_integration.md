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
*   **Communication**: Uses Qt Signals (`status_changed`, `start_failed`) to notify the UI
    about server state. `status_changed(True)` is emitted only after uvicorn completes
    `startup()` (socket bound and listening), not when the worker thread starts
    (PYPOST-556). Bind failures emit `start_failed(str)` with an operator-facing message and
    `status_changed(False)`.
*   **Shutdown**: Handles the complex logic of stopping `uvicorn` from another thread by setting flags and waiting for the thread to join.

### 2. `MCPServerImpl` (`pypost/core/mcp_server_impl.py`)

This class contains the actual business logic of the MCP server.

*   **Framework**: Uses `Starlette` + `mcp` SDK + `uvicorn`.
*   **Transport**: **Streamable HTTP** (current MCP spec) at `GET/POST /mcp`, with optional
    legacy **SSE** under `/sse` for backward-compatible clients.
    *   Primary: `http://<host>:<port>/mcp` — Streamable HTTP session (POST initialize,
      optional GET SSE stream for server messages).
    *   Legacy: GET `/sse/` + POST `/sse/messages` — deprecated HTTP+SSE transport.
*   **Route configuration (PYPOST-152)**: HTTP path constants live in
    `pypost/core/mcp_transport_routes.py` (`MCP_STREAMABLE_HTTP_PATH`,
    `MCP_LEGACY_SSE_MOUNT_PATH`, `MCP_LEGACY_SSE_MESSAGES_PATH`). `MCPServerImpl` and
    `MetricsServer` import these instead of hardcoding strings. Defaults match MCP spec /
    PyPost docs; change in one module if paths ever need updating.
*   **Tool Registration**: Converts `RequestData` objects (where `expose_as_mcp=True`) into MCP `Tool` definitions.
*   **Tool metadata (PYPOST-553)**: `RequestData.mcp_description` is the agent-visible
    description (falls back to `name`). `RequestData.mcp_params` holds per-parameter
    `McpToolParam` records (`type`, `description`, `required`).
*   **Schema Generation**: Discovers `{{ mcp.request.VAR_NAME }}` placeholders in URL,
    headers, params, and body (regex + optional `TemplateService` parse). Merges discovered
    names with explicit `mcp_params` and builds JSON Schema via `_build_tool_input_schema`.
    Undeclared placeholders default to `type: string`, `required: true` (backward compatible).
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
*   **MCP tools overview (PYPOST-556)**: Top-bar **MCP Tools (N)** opens
    `McpToolsOverviewDialog` with all `expose_as_mcp` requests across collections (MCP name,
    collection, method, description). Count refreshes on environment change.
*   **MCP activity log (PYPOST-141)**: Top-bar **MCP Activity (N)** opens
    `McpActivityDialog` with recent inbound `list_tools` and `call_tool` operations. Count
    reflects session entries; dialog live-refreshes while open via `activity_recorded`.
*   **Status label**: Shows `MCP: Starting (host:port)...` after `start_server` until
    `status_changed(True)`; `MCP: ON` only when listening; `start_failed` shows a warning
    dialog and resets to `MCP: OFF`.

### 4. Metrics observability stack (`pypost/core/metrics*.py`)

PyPost also exposes a separate MCP server dedicated to observability. PYPOST-75 split the
former monolithic `MetricsManager` into focused modules:

| Module | Class | Responsibility |
| --- | --- | --- |
| `pypost/core/metrics_registry.py` | `MetricsRegistry` | Prometheus counters and `track_*` methods (no I/O) |
| `pypost/core/metrics_server.py` | `MetricsServer` | MCP resources, Starlette app, uvicorn thread lifecycle |
| `pypost/core/metrics.py` | `MetricsManager` | Facade composed at `main.py`; same injection API as before |
| `pypost/core/server_bind.py` | `format_bind_error` | Shared operator-facing bind failure messages |

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
7.  After `startup()` completes, `MCPServerManager` emits `status_changed(True)`.
8.  On bind failure, `start_failed` carries a user-visible message; UI stays OFF.

### MCP tools overview (PYPOST-556)

`collect_mcp_tool_overview(collections)` in `pypost/core/mcp_tools_overview.py` builds
sorted `McpToolOverviewEntry` rows. `EnvPresenter` opens `McpToolsOverviewDialog` from the
top bar. Overview is read-only and does not require MCP to be running.

### MCP activity inspection (PYPOST-141)

`McpActivityLog` in `pypost/core/mcp_activity_log.py` stores a thread-safe ring buffer (default
100 entries) of `McpActivityEntry` records. `MCPServerImpl` appends on each `list_tools` and
`call_tool` invocation when a log is injected (via `MCPServerManager`).

| Field | `list_tools` | `call_tool` |
| --- | --- | --- |
| `operation` | `list_tools` | `call_tool` |
| `tool_count` | number of tools returned | — |
| `tool_name` | — | MCP tool name |
| `mcp_arg_count` | — | count of agent arguments (values never stored) |
| `http_status` | — | upstream HTTP status from execution |
| `duration_ms` | — | wall time for handler |
| `outcome` | `success` | `success` or `error` |
| `detail` | — | short error message when applicable |

`MCPServerManager.activity_recorded` emits each new entry for UI refresh. `EnvPresenter`
opens `McpActivityDialog` from **MCP Activity (N)** in the top bar.

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
6.  `RequestService.execute()` is called with the merged dict.
    -   It renders templates (environment placeholders **and** `{{ mcp.request.* }}`).
    -   Executes the HTTP request via `HTTPClient`.
    -   Runs any post-request scripts via `ScriptExecutor` (same variable dict as GUI).
7.  `format_structured_tool_result()` builds a JSON envelope (`status`, `error`, `body`,
    optional `logs`, `error_category`, `error_message`) returned as `TextContent`.

### Structured tool results (PYPOST-557)

Every execution-path `call_tool` response is JSON text with a fixed envelope:

| Field | Type | Description |
| --- | --- | --- |
| `status` | `int` | HTTP status from upstream; `0` when PyPost could not complete the request |
| `error` | `bool` | `true` when PyPost execution failed; `false` for completed HTTP calls (including 4xx/5xx) |
| `body` | `str` | Response body from upstream or synthetic error body |
| `logs` | `string[]` | Optional post-request script log lines |
| `error_category` | `string` | Optional `ErrorCategory` value when `execution_error` is set |
| `error_message` | `string` | Optional human-readable execution error message |

Example success:

```json
{"status": 200, "error": false, "body": "{\"id\": 1}"}
```

Example upstream 404 (not an execution error):

```json
{"status": 404, "error": false, "body": "Not Found"}
```

Example network failure:

```json
{
  "status": 0,
  "error": true,
  "body": "{\"error\": \"...\", \"detail\": \"...\"}",
  "error_category": "network",
  "error_message": "Could not connect to ..."
}
```

**Protocol errors** (unknown tool, unexpected internal exception) are **not** JSON envelopes —
unknown tools raise; internal failures return plain `Error executing request: …` text.

Metrics: `track_mcp_response_sent` uses outcome `"error"` when the envelope `error` flag is
`true`, else `"success"`.

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
wired on the execution path for masking — but **PYPOST-554** supplies `hidden_keys` to
`McpSecretsPolicy` so `list_tools` schemas exclude hidden and env-only placeholders. See
`doc/dev/mcp_secrets_policy.md`.

#### Observability

DEBUG log in `_build_execution_variables`: `mcp_execution_variables_merged` with
`env_var_count`, `hidden_key_count`, and `mcp_arg_count` (no names or values). See
`ai-tasks/PYPOST-554/50-observability.md` and `doc/dev/mcp_secrets_policy.md`.

## Threading Model

*   **Main Thread (Qt)**: UI, Dialogs, Settings.
*   **Worker Thread (`RequestWorker`)**: Used for GUI-initiated requests.
*   **MCP Thread (`MCPServerManager`)**: Runs the `uvicorn` loop.
    *   **Thread Pool**: Used inside MCP Thread for blocking I/O (Request execution).
    *   **Variable supplier**: Must not call Qt APIs. `EnvPresenter` reads only
        `_current_variables` (main-thread cache); supplier returns `dict(...)` snapshot.
*   **Metrics Thread (`MetricsServer` via `MetricsManager`)**: Runs its own isolated
    `uvicorn` loop for metrics and observability. Bind failures emit `start_failed(str)` on
    `MetricsManager` (PYPOST-153) with the same message style as MCP. `MainWindow` connects
    via `connect_start_failed` so failures during early startup are replayed. Success is logged
    as `metrics_server_listening`, not when the thread starts.

## API / Usage

### `MCPServerManager.set_variable_supplier(supplier)`

Register a callable that returns the current active environment variables as `dict[str, str]`.
Called by `EnvPresenter` at init. Forwarded to `MCPServerImpl`. Pass `None` to reset to an
empty dict.

### `MCPServerManager.set_hidden_keys_supplier(supplier)`

Register a callable returning the active environment's `hidden_keys` set. Called by
`EnvPresenter` at init. Used by `McpSecretsPolicy` during `list_tools` schema generation.

### `MCPServerImpl._build_execution_variables(mcp_args)`

Internal. Invokes `_variable_supplier()`, logs merge counts at DEBUG, returns merged dict for
`RequestService.execute()`.

### `_merge_execution_variables(env_vars, mcp_args)`

Pure merge helper; unit-tested independently. Spread env vars first, then set `"mcp"` from tool
arguments.

### `format_structured_tool_result(result)`

Public helper. Serializes `ExecutionResult` to the JSON envelope documented above.

### `_tool_result_has_error(result)`

Internal. Returns `true` when `execution_error` is set or `response.status_code == 0`.

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
| UI shows MCP ON but agent cannot connect | Status used to flip before bind (fixed PYPOST-556) or wrong port | Wait for ON after Starting; check Settings port; read `start_failed` dialog |
| Port busy on MCP start | Another process on `mcp_port` | Dialog explains conflict; free port or change Settings |

### Tool metadata authoring (PYPOST-553)

#### Model

| Field | Type | Notes |
| --- | --- | --- |
| `mcp_description` | `str` | Shown in `list_tools`; empty → `name` |
| `mcp_params` | `Dict[str, McpToolParam]` | Keyed by parameter name |

`McpToolParam`: `type` (`string`, `integer`, `number`, `boolean`, `array`, `object`),
`description`, `required` (default `True`).

#### Schema pipeline

```
McpSecretsPolicy.extract_mcp_request_variables(req)  ← regex on {{ mcp.request.VAR }}
        │
        ▼
resolve_mcp_param_specs(req, discovered)  ← merges mcp_params overrides
        │
        ▼
McpSecretsPolicy.filter_agent_param_specs(...)  ← drops env-only / hidden keys
        │
        ▼
build_tool_input_schema(specs)  → Tool.inputSchema
```

#### UI

`RequestWidget` **MCP** tab: tool description (`QPlainTextEdit`) and `McpParamsTable`
(name, type, description, required). Persisted via `_PERSISTED_FIELD_NAMES` in
`request_sync.py`.

#### Agent contract preview (PYPOST-555)

Read-only panel **Agent preview (list_tools)** on the MCP tab shows what local MCP clients
receive without starting the server or calling `list_tools` over HTTP.

| Preview section | Source |
| --- | --- |
| Tool name | `normalize_mcp_tool_name(request.name)` |
| Description | `tool_description(request)` |
| `inputSchema` | `build_tool_input_schema` after `McpSecretsPolicy.filter_agent_param_specs` |
| Hidden variable policy | Names excluded as `hidden env key` or `env-only` |

Implementation: `pypost/core/mcp_tool_contract.py` (`build_mcp_tool_contract_preview`,
`format_mcp_tool_contract_preview`). Shared helpers (`tool_description`,
`resolve_mcp_param_specs`, `build_tool_input_schema`) are also used by `MCPServerImpl`.

The preview refreshes when MCP metadata or template-bearing fields change and when
`set_hidden_keys` / `set_template_service` run (wired from `TabsPresenter` and
`env_hidden_keys_changed`).

## Limitations & Tech Debt

*   **Synchronous Execution**: The core uses `requests` (sync). Ideally, we should move to `httpx` for async support to avoid `run_in_threadpool`.
*   **Parsing**: Schema generation uses `TemplateService` for AST parsing, but complex Jinja2 constructs might still need attention.
*   **Schema vs execution**: `list_tools` JSON Schema lists `mcp.request.*` placeholders
    (plus non-forbidden explicit `mcp_params`); environment and hidden variables are resolved
    at execution time and are not listed as tool inputs (PYPOST-554).
*   **UI sync**: MCP params table is manual; auto-populate from template scan is deferred (see `ai-tasks/PYPOST-553/60-tech-debt.md`).
*   **Dual variable sources in EnvPresenter**: `current_variables` property reads the combo box while MCP uses `_current_variables` cache (see `ai-tasks/PYPOST-550/60-tech-debt.md`).

See `ai-tasks/PYPOST-20/40-tech-debt.md` for more details.
