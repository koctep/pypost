# MCP Integration (Developer Guide)

See also [PyPost MCP Integration](../mcp_integration.md) for user-facing setup, client
configuration (Cursor, Claude Desktop), and operator troubleshooting.
See also [MCP Reverse Proxy](mcp_proxy.md) (PYPOST-1092) for the reverse proxy mode forwarding requests to upstream MCP servers.

This document describes the internal implementation of the **Model Context Protocol (MCP)** server within PyPost.

## Overview

PyPost implements an **MCP Server** using the official Python SDK (`mcp`). This allows external MCP Clients (like Claude Desktop or Cursor) to connect to PyPost and execute HTTP requests defined in the user's collections as "Tools".

**Not the same as agent UI e2e:** in-process offscreen harness tests
(`make test-agent-e2e`) drive the Qt UI without a live MCP client — see
[agent_e2e.md](agent_e2e.md). MCP below assumes a running PyPost with the MCP
server enabled.

**UI actions are not product MCP tools:** click / fill / select / send key
live in `pypost.agent.ui_actions` (in-process) or the dedicated stdio sidecar
([agent_ui_actions_mcp.md](agent_ui_actions_mcp.md), PYPOST-952). Out-of-process
packaging must use that entry — never register on `MCPServerImpl`. See also
[ui_actions.md](ui_actions.md) (PYPOST-918).

**Security:** Inbound MCP has no client authentication. Default bind is loopback-only; see
[mcp_trust_model.md](mcp_trust_model.md) before exposing MCP on a network.

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
*   **Legacy SSE module (PYPOST-156)**: `SSEEndpoint`, `MessagesEndpoint`, and
    `build_legacy_sse_app()` live in `pypost/core/mcp_legacy_sse.py`. Both `MCPServerImpl` and
    `MetricsServer` delegate `_create_sse_app()` to this factory so endpoints are importable
    and unit-testable without nesting inside server classes.
*   **Legacy SSE routing (PYPOST-155)**: Inside the `/sse` sub-app, Starlette `Route` entries
    enforce HTTP methods declaratively: `GET /` for the SSE stream and
    `POST {MCP_LEGACY_SSE_MESSAGES_PATH}` for client messages. Endpoints remain ASGI callables
    because the MCP SDK's `connect_sse` and `handle_post_message` write directly to the ASGI
    `send` channel. Wrong methods receive 405 from Starlette routing, not manual ASGI responses.
    The outer `Mount` on `MCP_LEGACY_SSE_MOUNT_PATH` has no method filter (e.g. POST `/sse`
    returns 405).
*   **MessagesEndpoint responses (PYPOST-157)**: `MessagesEndpoint` in `mcp_legacy_sse.py` is a
    pure ASGI delegate to `handle_post_message` — no `starlette.responses` usage and no manual
    `_send_response` / raw ASGI status bodies. Module-level `Response` is used only by the GET
    SSE wrapper (`handle_sse_get`) after the stream completes.
*   **Legacy SSE ASGI efficiency (PYPOST-159)**: Performance is not a concern for this transport.
    Starlette `Mount` on `MCP_LEGACY_SSE_MOUNT_PATH` forwards `scope` / `receive` / `send` to the
    inner `Starlette` sub-app without a `request_response` adapter — the same pattern as
    Prometheus on `/metrics`. Inside the sub-app, `MessagesEndpoint` is registered on `Route` as a
    direct ASGI callable (`route.app` remains the endpoint instance; see
    `tests/test_mcp_asgi_compatibility.py`). That path is at least as efficient as a
    `request_response` wrapper. GET `/` alone uses `handle_sse_get`, an async function returning
    `Response` after `connect_sse` teardown — Starlette wraps it once in `request_response`. The
    overhead is negligible for long-lived SSE connections and avoids `TypeError` on `await None`
    from the original PYPOST-21 bug. Do not replace outer `Mount` with `Route` expecting a perf
    win; `Mount` is already the efficient ASGI delegation pattern.
*   **Tool Registration**: Converts `RequestData` objects (where `expose_as_mcp=True`) into MCP `Tool` definitions.
*   **Tool metadata (PYPOST-553)**: `RequestData.mcp_description` is the agent-visible
    description (falls back to `name`). `RequestData.mcp_params` holds per-parameter
    `McpToolParam` records (`type`, `description`, `required`, `default` — PYPOST-1054, see
    [Optional MCP parameter defaults](#optional-mcp-parameter-defaults-pypost-1054) below).
*   **Schema Generation (PYPOST-1052)**: Discovers `mcp.request.VAR_NAME` placeholders
    across URL, headers, params, and body—supporting both bare (e.g. `{{ mcp.request.x }}`)
    and function-wrapped expressions (e.g. `{{ to_int(mcp.request.id) }}`)—via regex in
    `McpSecretsPolicy.extract_mcp_request_variables`. Merges discovered names with
    explicit `mcp_params` and builds JSON Schema via `build_tool_input_schema`.
    Undeclared placeholders default to `type: string`, `required: true` (backward compatible).
*   **Execution**: Delegates request execution to a fresh `RequestService` per `call_tool`
    invocation so each MCP tool call owns an isolated `HTTPClient` / `requests.Session`
    (PYPOST-138). Synchronous work runs in Starlette's threadpool via
    `run_in_threadpool`, capped at **4** concurrent `call_tool` executions per server
    instance (`asyncio.Semaphore` in `MCPServerImpl`, PYPOST-759).
*   **Environment variables (PYPOST-550)**: At `call_tool` time, reads the endpoint's
    configured environment snapshot via an injected `variable_supplier`, merges it with MCP
    tool arguments, and passes the combined dict to `RequestService.execute()` (GUI parity).

### 3. Multiple-endpoint registry (`pypost/core/mcp_server_registry.py`, PYPOST-1044)

The application-level lifecycle owner is `MCPServerRegistry`: it maps every
persisted `McpServerConfiguration` to its own `MCPServerManager` /
`MCPServerImpl` runtime. Each row selects one collection, environment, host,
and globally unique port. Requests and environment/hidden-key values are
copied into that runtime, preventing UI selection from retargeting another
endpoint. See [Multiple MCP Servers](mcp_server_registry.md) for the API,
persistence, migration, observability, and troubleshooting details.

### 4. `McpServerSettingsController` (`pypost/ui/mcp_server_controller.py`, PYPOST-1071)

The UI-side owner of MCP **persistence and lifecycle**. PYPOST-1044 placed this behaviour in
`MainWindow`; PYPOST-1071 extracted it, leaving the window as composition root plus startup
readiness gate.

*   **Responsibility**: Build (or accept an injected) `MCPServerRegistry` and
    `MCPServerManager`, load persisted rows at construction, mutate
    `AppSettings.mcp_servers` and save through `ConfigManager`, and issue per-endpoint
    start / stop / remove / reconfigure commands.
*   **Construction**: `MainWindow` instantiates
    `McpServerSettingsController(settings_provider=…, config_manager=…, collection_lookup=…, environment_lookup=…, metrics=…, template_service=…, mcp_manager=…, registry=…)`
    (`pypost/ui/main_window.py:107`), directly passing collaborator lookup callables. `MainWindow` no longer re-publishes `mcp_manager` or `mcp_registry` attribute aliases (PYPOST-1085).
*   **Readiness gate**: `start_enabled()` is a pass-through the window calls only from
    `_maybe_complete_startup_restore()` (`pypost/ui/main_window.py:166`), after both
    collections and environments have loaded. `stop_all()` runs at shutdown.
*   **Transactional edits**: it connects to `MCPServerRegistry.reconfiguration_finished`
    and persists a running-row edit **only** when the replacement endpoint bound
    (`committed=true`).
*   **Protocol surface**: it satisfies the `McpServerController` protocol consumed by the
    controls presenter — `mcp_server_configurations`, `mcp_server_count`, `mcp_server_status`,
    `mcp_server_activity`, `upsert_mcp_server`, `remove_mcp_server`, `start_mcp_server`,
    `stop_mcp_server`. Configuration rows from `mcp_server_configurations` are returned as
    deep copies; `mcp_server_count` (PYPOST-1083) returns `len(self._settings.mcp_servers)`
    directly, so call sites that only need the row count — e.g. the
    `mcp_servers_dialog_opened` log line in `McpControlsPresenter._open_mcp_servers` — no
    longer pay for a deep copy just to log it.

### 5. `McpControlsPresenter` (`pypost/ui/presenters/mcp_controls_presenter.py`, PYPOST-1071)

The UI-side owner of the **MCP portion of the environment bar**: status label, the three
buttons, the dialogs behind them, and scoped registry refreshes. Extracted from
`EnvPresenter` by PYPOST-1071.

*   **Widgets**: `widgets` returns **MCP Tools**, **MCP Activity**, **MCP Servers…** and the
    status label in display order; `EnvPresenter` inserts them into its bar layout.
*   **Status label**: With a registry it shows aggregate running/failed counts, not a
    potentially misleading endpoint. Row-specific state and errors live in the dialog.
*   **MCP tools overview**: With a registry, the top-bar button becomes **MCP Server Tools…**
    and opens the MCP Servers dialog; **Tools…** inside it is scoped to the selected row's
    collection. Without a registry it opens `McpToolsOverviewDialog` for the aggregate
    legacy catalog.
*   **MCP activity log**: The top-bar **MCP Activity (N)** view remains the legacy
    single-manager feed; the registry dialog exposes activity per selected endpoint.
*   **Server controller**: `MainWindow` calls `env.set_mcp_server_controller(...)`
    (`pypost/ui/main_window.py:130`), which forwards to
    `McpControlsPresenter.set_server_controller`. Without it, **MCP Servers…** logs
    `mcp_servers_dialog_no_controller` and does nothing.
*   **Legacy adapter**: `handle_environment_selected` applies the old
    `Environment.enable_mcp` start/stop rule, and `legacy_server_running()` reports it —
    both are no-ops once a registry is configured.

### 6. `EnvPresenter` (`pypost/ui/presenters/env_presenter.py`)

The environment selector owns environment state and variable propagation. After PYPOST-1071
it owns no MCP status, dialog or lifecycle code.

*   **Responsibility**: Load environments, emit variable changes to the UI, and delegate
    every MCP concern to `McpControlsPresenter`.
*   **Variable cache**: `EnvVariableSnapshot` is updated on the main thread in
    `_on_env_changed` whenever the user selects or edits an environment.
*   **Supplier registration**: On init, calls
    `MCPServerManager.set_variable_supplier(self._env_snapshot.snapshot_variables)`.
    The snapshot returns a **copy** so MCP threadpool workers never observe partial writes.
*   **Retired `mcp_*` shims (PYPOST-1082)**: Legacy delegating methods (`refresh_mcp_tools()`,
    `mcp_status_text()`, `mcp_tools_button_text()`, and `mcp_activity_button_text()`) were
    retired in PYPOST-1082. `EnvPresenter` exposes the public property `mcp_controls` returning
    its embedded `McpControlsPresenter` instance, and `MainWindow` exposes `mcp_controls`
    directly. Signal wiring in `pypost/ui/main_window_signals.py` connects directly to
    `window.mcp_controls.refresh_tools`. See [Presenter Architecture](presenter_architecture.md).

### 7. Metrics observability stack (`pypost/core/metrics*.py`)

PyPost also exposes a separate MCP server dedicated to observability. PYPOST-75 split the
former monolithic `MetricsManager` into focused modules:

| Module | Class | Responsibility |
| --- | --- | --- |
| `pypost/core/metrics_registry.py` | `MetricsRegistry` | Prometheus counters and `track_*` methods (no I/O); init split into `_init_gui_metrics`, `_init_http_metrics`, `_init_mcp_metrics`, `_init_encryption_metrics` (PYPOST-746) |
| `pypost/core/metrics_otel.py` | `OtelMetricsTracker` | OTel-backed `MetricsTrackerProtocol` adapter (PYPOST-579) |
| `pypost/core/metrics_server.py` | `MetricsServer` | MCP resources, Starlette app, uvicorn thread lifecycle |
| `pypost/core/metrics.py` | `MetricsManager` | Facade composed at `main.py`; same injection API as before |
| `pypost/core/server_bind.py` | `format_bind_error`, `drain_pending_tasks` | Shared bind-failure messages and asyncio loop teardown before `loop.close()` (PYPOST-726) |

*   **Role**: Provides application metrics via MCP Resources.
*   **Operator catalog**: Full metric names, types, labels, and meanings —
    [Prometheus Monitoring](../prometheus_monitoring.md#metric-inventory).
*   **Framework**: Same stack as the main server (`Starlette` + `mcp` SDK + `uvicorn`).
*   **Hybrid Server**: Hosts Prometheus (`/metrics`), Streamable HTTP MCP (`/mcp`), and
    legacy SSE (`/sse`, `/messages`) on the same port (default 9080).
*   **Declarative routing (PYPOST-166)**: `MetricsServer._create_app()` registers routes via
    Starlette `Mount` / `Route` — not manual `PATH_INFO` checks. Prometheus uses
    `Mount("/metrics", app=make_asgi_app(...))`; the `MetricsManager` facade has no HTTP
    routing logic.
*   **Resources**:
    *   `metrics://all`: Returns the full Prometheus metrics dump as `text/plain`.

## Key Flows

### Server Startup

1.  `McpServerSettingsController` loads every persisted `AppSettings.mcp_servers`
    row into `MCPServerRegistry` while the window composes it, and logs
    `mcp_persisted_servers_loaded count=… enabled_count=…`.
2.  After collections and environments are both loaded, `MainWindow` calls
    `mcp_controller.start_enabled()`, which starts each enabled row independently.
3.  `start(id)` resolves the row's collection and environment by ID, then copies
    its requests, variables, and hidden keys into that endpoint's manager.
4.  The endpoint's `MCPServerManager` creates a new thread; its
    `MCPServerImpl.create_app()` builds the Starlette app and
    `uvicorn.Server.serve()` binds the row's host/port.
5.  After `startup()` completes, the manager's signal updates only the matching
    registry row to `running`.
6.  A missing reference or bind failure marks only that row `failed`; other
    enabled endpoints continue starting and running.

### Server shutdown (PYPOST-726)

When uvicorn's `serve()` returns, SSE transports may still have a pending
`_shutdown_watcher` task on the loop. Before `loop.close()`, each `_run_uvicorn`
implementation calls `drain_pending_tasks(loop)` from `server_bind.py` to cancel and
await outstanding tasks, preventing spurious `Task was destroyed but it is pending!`
asyncio warnings in logs and test output.

### Metrics server startup (PYPOST-153 / PYPOST-154)

1.  `main.py` creates `MetricsManager` and calls `start_server(metrics_host, metrics_port)`
    before `MainWindow` is constructed.
2.  `MetricsServer` runs uvicorn in a background thread (same pattern as MCP).
3.  After `startup()` completes, logs `metrics_server_listening`.
4.  On bind failure, `MetricsManager.start_failed` carries a user-visible message.
5.  `MainWindow.connect_start_failed` replays failures that occurred before the window opened
    and shows `QMessageBox.warning` via `_on_metrics_start_failed`.

### Metrics server lifecycle locking (PYPOST-171)

`MetricsServer` owns `server_lock` (`threading.Lock`) for start/stop only. `MetricsManager`
delegates lifecycle calls without adding its own lock.

*   **Guarded state**: daemon `thread`, `server_instance`, and join during `stop_server`.
*   **Callers**: `main.py` (`start_server` at boot, `stop_server` at shutdown) and
    `MainWindow` (`restart_server` when metrics host/port change). All run on the Qt main
    thread today — infrequent, serialized lifecycle operations.
*   **Counters**: `track_*` methods do not take `server_lock`; Prometheus registry handles
    concurrent increments from workers and the metrics thread.
*   **Restart**: `restart_server` calls `stop_server` then `start_server` (two lock
    acquisitions). Acceptable while only the main thread invokes lifecycle methods.
*   **Caveat**: `start_server` may call `stop_server` while holding a non-reentrant `Lock`
    if a previous thread is still alive. Production uses `restart_server` for that case;
    do not add concurrent lifecycle callers without revisiting lock type or inlining stop.

### MCP tools overview (PYPOST-556)

`collect_mcp_tool_overview(collections)` in `pypost/core/mcp_tools_overview.py` builds
sorted `McpToolOverviewEntry` rows. `McpControlsPresenter` opens `McpToolsOverviewDialog`
from the top bar (`mcp_tools_overview_opened tool_count=…`). Overview is read-only and does
not require MCP to be running.

### Scoped tool list refresh

When the user saves a request or edits collections while MCP is running, PyPost must expose an
up-to-date tool catalog to connected agents.

1.  `wire_presenter_signals` connects collection changes to
    `window.mcp_controls.refresh_tools()` (`pypost/ui/main_window_signals.py:18,21,31`)
    on `McpControlsPresenter`.
2.  With a registry, the controls presenter first reconciles missing
    collection/environment references and then calls `refresh_collection(id)` for each
    current collection.
3.  The registry updates only managers whose configuration selected that collection.
    `MCPServerManager.update_tools()` compares its local tool signature and restarts
    only that endpoint when the signature changed.
4.  The top-bar action becomes **MCP Server Tools…**, which opens a row-specific
    tools view rather than an aggregate catalog.

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

Each registry-owned manager has its own activity log. `McpServersDialog` opens
`McpActivityDialog` for the selected endpoint through
`McpServerSettingsController.mcp_server_activity()`, which returns `[]` and logs
`mcp_server_activity_unavailable instance_id=…` at DEBUG when that endpoint has never
started. The top-bar **MCP Activity (N)** remains the legacy single-manager view and is not
an aggregate registry activity feed.

### Tool Execution

1.  External Client sends a `call_tool` request via Streamable HTTP (`/mcp`).
2.  `MCPServerImpl.call_tool` is invoked (async).
3.  **Context Switching**: Since `RequestService` is synchronous, execution is offloaded to a thread pool using `starlette.concurrency.run_in_threadpool`.
4.  `_execute_request_sync` builds the variables dict:
    -   Calls `variable_supplier()` for the endpoint's flat environment snapshot
        (e.g. `base_url`, `api_key`).
    -   Merges with MCP tool arguments via `_merge_execution_variables` (see below).
5.  `_create_request_service()` builds a new `RequestService` (and `HTTPClient`) for this call.
6.  `RequestService.execute()` is called with the merged dict.
    -   It renders templates (environment placeholders **and** `{{ mcp.request.* }}`).
    -   Executes the HTTP request via `HTTPClient`.
    -   Runs any post-request scripts via `ScriptExecutor` (same variable dict as GUI).
7.  `format_structured_tool_result()` builds a JSON envelope (`status`, `error`, `body`,
    optional `logs`, `error_category`, `error_message`, `error_detail`) returned as
    `TextContent`.

### Structured tool results (PYPOST-557)

Every execution-path `call_tool` response is JSON text with a fixed envelope. Upstream
response bodies and post-script `logs` are passed through
`McpResponseSanitizer` (PYPOST-703) before agents see them: hidden environment values,
common JSON credential fields, `Bearer` tokens, and sensitive query parameters are
redacted to `***`.

| Field | Type | Description |
| --- | --- | --- |
| `status` | `int` | HTTP status from upstream; `0` when PyPost could not complete the request |
| `error` | `bool` | `true` when PyPost execution failed; `false` for completed HTTP calls (including 4xx/5xx) |
| `body` | `str` | Sanitized upstream response body (`***` redactions for secrets) |
| `logs` | `string[]` | Optional post-request script log lines (sanitized like `body`) |
| `error_category` | `string` | Optional `ErrorCategory` value when `execution_error` is set |
| `error_message` | `string` | Optional human-readable execution error message |
| `error_detail` | `string` | Optional technical detail from `ExecutionError.detail` (sanitized like `body`) |

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
  "error_message": "Could not connect to ...",
  "error_detail": "Connection refused: ..."
}
```

**Protocol errors** (unknown tool, unexpected internal exception) are **not** JSON envelopes —
unknown tools raise; internal failures return plain `Error executing request: …` text.

#### Agent parsing (PYPOST-680)

MCP clients receive the envelope as a string in `TextContent.text`. **Always** parse before
using fields — do not assume the text is the upstream HTTP body.

```python
import json

envelope = json.loads(text_content.text)
status = envelope["status"]
failed = envelope["error"]
body = envelope["body"]
logs = envelope.get("logs", [])
```

| Consumer | Guidance |
| --- | --- |
| AI agents (Cursor, Claude Desktop) | Parse JSON on every successful `call_tool`; check `error` before `body` |
| Custom MCP clients | Same as integration tests: `json.loads(result.content[0].text)` |
| Operators | User-facing setup: [mcp_integration.md](../mcp_integration.md#tool-call-responses-json-envelope) |

`error: false` with `status: 404` means PyPost executed successfully and the upstream API
returned 404. `error: true` with `status: 0` means PyPost failed before a normal HTTP
response (network, template, script).

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
| `{{ base_url }}` | top-level key | Configured endpoint environment snapshot |
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
MCPServerRegistry._runtime_inputs(configuration)
        │  copies variables from configuration.environment_id
        ▼  set_variable_supplier(λ: dict(snapshot))
MCPServerManager ──► MCPServerImpl._variable_supplier
        │
        ▼  per call_tool (threadpool worker)
_build_execution_variables(mcp_args) ──► RequestService.execute(request, merged)
```

Freshness: the supplier is invoked on **every** `call_tool`. `refresh_environment(id)` replaces
the snapshot only for endpoints selecting that environment; a top-bar selection change has no
effect. The legacy `EnvPresenter` cache wiring remains compatibility-only.

### Optional MCP parameter defaults (PYPOST-1054)

Follow-up from [PYPOST-1029](https://pypost.atlassian.net/browse/PYPOST-1029) TD-1: curated
Jira MCP list tools originally had to mark `maxResults` / `startAt` `required: true` because
omitting them failed template rendering (`to_int(mcp.request.maxResults)` on a missing key).
PYPOST-1054 adds a general-purpose `default` value to `McpToolParam` so any optional MCP
parameter can declare a safe fallback that is both agent-discoverable (published in the
JSON Schema) and applied automatically at execution time when the caller omits the argument.

#### Model field

`McpToolParam.default: Optional[Any] = None` (`pypost/models/models.py`). `None` means "no
default declared" — it is not itself a usable default value (a curated tool cannot currently
express "the true default is `null`"; see Limitations). Defaults to `None`, so every
pre-existing collection JSON without a `default` key is unaffected.

#### Schema publication

`build_tool_input_schema` (`pypost/core/mcp_tool_contract.py`) adds `prop["default"] =
spec.default` to a parameter's JSON Schema property whenever `spec.default is not None`,
alongside the pre-existing `required`-list exclusion for `spec.required is False`. Agents see
the default in `list_tools`'s `inputSchema` without needing an extra call or documentation
lookup.

#### Execution-time defaulting

`MCPServerImpl._build_execution_variables` (`pypost/core/mcp_server_impl.py`) takes an
optional `request_data: RequestData | None = None` fourth argument. When supplied, it walks
`request_data.mcp_params` and, for each `param_spec.default is not None`, fills
`merged_args[param_name]` from that default whenever the caller's `mcp_args` **either omits
the key or explicitly passes `None`/`null`** for it — so `{"maxResults": null}` defaults just
like omitting `maxResults` entirely. `_execute_request_sync` always passes the current
`request_data` through, so this applies to every MCP tool call, not just the curated Jira
fixtures. Explicit non-`None` values (including numeric strings like `"25"` for
`integer_or_string` params) always win over the declared default.

```python
def _build_execution_variables(
    self,
    mcp_args: dict[str, Any],
    env_vars: dict[str, str],
    hidden_keys: set[str],
    request_data: RequestData | None = None,
) -> dict[str, Any]:
    merged_args = dict(mcp_args or {})
    defaults_applied = 0
    if request_data is not None and request_data.mcp_params:
        for param_name, param_spec in request_data.mcp_params.items():
            if (
                param_name not in merged_args
                or merged_args[param_name] is None
            ) and param_spec.default is not None:
                merged_args[param_name] = param_spec.default
                defaults_applied += 1
                self._metrics.track_mcp_param_default_applied(request_data.method)
                logger.info(
                    "mcp_param_default_applied method=%s param=%s default=%r",
                    request_data.method, param_name, param_spec.default,
                )
    counts = McpSecretsPolicy.safe_execution_log_fields(
        len(env_vars), len(hidden_keys), len(merged_args)
    )
    logger.debug(
        "mcp_execution_variables_merged env_var_count=%d "
        "hidden_key_count=%d mcp_arg_count=%d defaults_applied_count=%d",
        counts["env_var_count"], counts["hidden_key_count"],
        counts["mcp_arg_count"], defaults_applied,
    )
    execution_env = McpSecretsPolicy.execution_environment_variables(env_vars)
    return _merge_execution_variables(execution_env, merged_args)
```

#### Observability (log + metric)

*   **INFO log**: `mcp_param_default_applied method=%s param=%s default=%r`, emitted once per
    parameter actually defaulted (`param` is the declared MCP param name, e.g. `maxResults`;
    `default` is the static value substituted, e.g. `50`). Neither field is sensitive — both
    are already public via the `list_tools` JSON Schema.
*   **DEBUG log**: the pre-existing `mcp_execution_variables_merged` line gained a
    `defaults_applied_count=%d` field. `mcp_arg_count` counts `merged_args` (post-defaulting);
    the caller's raw argument count can be recovered via `(mcp_arg_count - defaults_applied_count)`
    (clarified in PYPOST-1090).
*   **Counter**: `mcp_param_defaults_applied_total{method}` (Prometheus + OTel), incremented
    once per defaulted parameter alongside the INFO log — the same "counter + log at the point
    of silent substitution" convention as `track_response_body_truncated` in `http_client.py`.
    Labeled only by the coarse HTTP `method`, never by parameter name, to avoid unbounded
    label cardinality from user-authored tools. Threaded through all four
    `MetricsTrackerProtocol` implementers (`metrics_protocol.py`, `metrics_registry.py`,
    `metrics_otel.py`, `qt/metrics.py`) via `track_mcp_param_default_applied(method)`.

#### UI round-trip

`McpParamsTable` exposes `default` through an editable **Default** column
(PYPOST-1089) — see [Tool metadata authoring § UI](#ui) below.

#### Curated Jira fixtures

`examples/collections/jira_mcp.json`'s `jira-list-boards`, `jira-list-board-sprints`, and
`jira-get-sprint-issues` now declare `maxResults` (`default: 50`) and `startAt`
(`default: 0`) as `required: false` instead of `required: true`. Calling these tools with `{}`
now resolves `mcp.request.maxResults` / `mcp.request.startAt` to `50` / `0` instead of failing
template render. Explicit custom values are still honored unchanged. See
[Jira MCP Example Project Default § List pagination](jira_mcp_project_default.md#list-pagination-pypost-1029--pypost-1054)
for the fixture-level writeup and
[jira-mcp example fixtures contract](testing.md#example-fixtures-contract-pypost-1017--pypost-1026--pypost-1047--pypost-1028--pypost-1048--pypost-1050--pypost-1056)
for the test coverage.

#### Limitations

*   `default`'s Python type **is** now cross-checked against the parameter's declared
    `type` at construction time (PYPOST-1089) — see
    [Default value type validation](#default-value-type-validation-pypost-1089) below.
    That check only covers the *declared* default, not MCP arguments actually supplied by
    a caller at execution time; extending it to `mcp_args` in
    `_build_execution_variables` is tracked as
    [PYPOST-1100](https://pypost.atlassian.net/browse/PYPOST-1100).
*   The GUI now has an editable **Default** column (PYPOST-1089) — see
    [UI](#ui) above. The column is a plain-text cell for every type (no checkbox for
    `boolean`, no JSON editor for `array`/`object`); a type-aware editor is tracked as
    [PYPOST-1099](https://pypost.atlassian.net/browse/PYPOST-1099).
*   Four curated Jira list tools (`jira-list-boards`, `jira-list-board-sprints`,
    `jira-get-sprint-issues`, `jira-search-assignable-users`) ship the optional pagination
    pattern with safe defaults (50, 0) (PYPOST-1054, PYPOST-1091). `jira-search-issues-jql`
    carries explicit pagination guidance in its description for its `search_payload` body.

See `ai-tasks/PYPOST-1054/60-tech-debt.md` for the full analysis.

### Default value type validation (PYPOST-1089)

`McpToolParam` validates that `default` (when not `None`) is a Python value compatible
with the declared `type`, closing the gap noted above.

#### Implementation

Validation runs from a **`model_post_init` hook**, not a `@model_validator`-decorated
method — the same convention already used by `Settings` elsewhere in `models.py`. Do
not go looking for a `@model_validator` decorator on `McpToolParam`; there isn't one
(documentation gap called out by
[PYPOST-1098](https://pypost.atlassian.net/browse/PYPOST-1098)).

```python
def model_post_init(self, __context) -> None:
    if self.type not in _MCP_PARAM_TYPES:
        raise ValueError(f"Unsupported MCP param type: {self.type}")
    self._validate_default_type()
```

`McpToolParam._validate_default_type()` (`pypost/models/models.py`) raises `ValueError`
on a mismatch, which Pydantic converts to `ValidationError` at construction time
(`McpToolParam(...)`, including when Pydantic rebuilds a model from stored/imported
collection JSON).

#### Type compatibility rules

| Declared `type` | Accepted Python type(s) for `default` |
| --- | --- |
| `string` | `str` |
| `integer` | `int`, excluding `bool` |
| `integer_or_string` | `int` or `str`, excluding `bool` |
| `number` | `int` or `float`, excluding `bool` |
| `boolean` | `bool` |
| `array` | `list` |
| `object` | `dict` |

*   **`None` is always permitted** regardless of `type` — it means "no default
    declared", not "the default is `null`" (see
    [Optional MCP parameter defaults § Model field](#model-field) above).
*   **`bool` is explicitly excluded** from `integer`, `number`, and `integer_or_string`
    because Python's `bool` is an `int` subclass (`isinstance(True, int)` is `True`); each
    check adds `and not isinstance(value, bool)` so `McpToolParam(type="integer",
    default=True)` still raises.

#### Where this can surface

*   **Direct construction**: `McpToolParam(type="boolean", default="fifty")` now raises
    `pydantic.ValidationError` instead of constructing silently.
*   **Loading untrusted data**: `StorageManager.load_collections()`
    (`pypost/core/storage.py`, `logger.warning("storage_collection_load_failed …")`) and
    `load_collection_import_candidates()` (`pypost/core/collection_import.py`, per-record
    `parse_errors` surfaced via the import dialog) already catch and log/report
    construction errors per-record — see `ai-tasks/PYPOST-1089/50-observability.md` for
    the full trace. A malformed `default` in a hand-edited or imported collection file
    now surfaces as a load/import error rather than a downstream schema or
    template-render failure.
*   **The MCP params table (GUI)** cannot trigger this in practice: `McpParamsTable`'s
    `_COERCERS` (see [UI](#ui) above) only ever produce a type-matched value or `None`
    before `McpToolParam` is constructed from `get_data()`.

### MCP argument substitution coverage (PYPOST-1034)

MCP tool arguments are available to request templates below the protected
`mcp.request` namespace.  The normal request-rendering path applies those values
to the URL, headers, query parameters, and a request body before HTTP transport.
For example, the shipped Jira MCP collection uses:

| Jira MCP request | Request location | Template | MCP tool argument |
| --- | --- | --- | --- |
| `jira-search-fields` | Query parameter `query` | `{{ mcp.request.query }}` | `query` |
| `jira-search-issues-jql` | Complete JSON body | `{{ mcp.request.search_payload }}` | `search_payload` |

`search_payload` is a string because it occupies the complete JSON request-body
template; callers supply serialized JSON, such as
`json.dumps({"jql": "project = DEMO", "maxResults": 1})`.  The HTTP client
renders the string first and then parses/sends it as JSON.  Tool and argument
names, collection content, and production APIs are unchanged by this coverage.

#### Regression test boundary

`tests/test_mcp_server_integration.py` contains two live Streamable HTTP MCP
round trips for the table above.  Each test imports `examples/collections/jira_mcp.json`,
deep-copies the selected request, and replaces only its URL with a local
`ThreadingHTTPServer`.  This keeps the published Jira request shape as the source
of truth while avoiding Jira credentials, network access, and real-project mutation.

The loopback handler records the outbound request, and the test asserts both the
normal MCP success envelope (`error: false`, `status: 200`) and rendered wire
data.  The query scenario verifies the decoded `query` value is `Story Point`;
the JSON-body scenario verifies the decoded body equals the client-provided object.  Literal
`mcp.request` or template braces therefore fail the tests rather than silently
reaching an upstream service.

Run the focused regression pair with the project test target:

```bash
PYTEST_ARGS="tests/test_mcp_server_integration.py::TestMCPServerIntegration::test_call_tool_substitutes_jira_mcp_query_parameter tests/test_mcp_server_integration.py::TestMCPServerIntegration::test_call_tool_substitutes_jira_mcp_json_body" make test
```

### Jira numeric path identifiers (PYPOST-1038)

The shipped Jira MCP collection has a deliberately narrow dual-form identifier
contract for its board/sprint path arguments. Collection authors declare these
arguments as `integer_or_string`; the published MCP JSON Schema is an `anyOf`
of a native JSON `integer` and a decimal JSON `string` matching
`^[+-]?[0-9]+$`. This is not a general coercion rule for MCP parameters.

| Request id | MCP argument | Jira path |
| --- | --- | --- |
| `jira-list-board-sprints` | `board_id` | `/rest/agile/1.0/board/{boardId}/sprint` |
| `jira-get-sprint` | `sprint_id` | `/rest/agile/1.0/sprint/{sprintId}` |
| `jira-update-sprint` | `sprint_id` | `/rest/agile/1.0/sprint/{sprintId}` |
| `jira-delete-sprint` | `sprint_id` | `/rest/agile/1.0/sprint/{sprintId}` |
| `jira-add-issues-to-sprint` | `sprint_id` | `/rest/agile/1.0/sprint/{sprintId}/issue` |
| `jira-get-sprint-issues` | `sprint_id` | `/rest/agile/1.0/sprint/{sprintId}/issue` |

Each path uses `{{ to_int(mcp.request.<argument>) }}`. Thus both `"42"` and
`42` render as `/42`; booleans, floats, and non-decimal strings fail during
HTTP request preparation and no request is dispatched. The union only widens
these six client-facing input schemas; it does not change tool names,
argument names, Jira endpoints, or serialized payload arguments.

`tests/test_example_fixtures.py` locks the complete six-row mapping and the
published descriptions/templates. The real Streamable HTTP tests in
`tests/test_mcp_server_integration.py` invoke every row with both valid forms
against a local loopback server and assert invalid string/float identifiers
never reach it. Run that focused coverage with:

```bash
PYTEST_ARGS="tests/test_example_fixtures.py tests/test_mcp_server_integration.py::TestMCPServerIntegration::test_jira_numeric_path_identifiers_accept_decimal_strings_and_native_integers tests/test_mcp_server_integration.py::TestMCPServerIntegration::test_jira_non_integral_identifier_never_dispatches_to_http" make test
```

### Optional protected Jira live smoke (PYPOST-1039)

The shipped Jira MCP example also has a narrowly scoped **opt-in** live smoke
for authorized maintainers. It runs only through `make test-jira-mcp-live` and
uses the explicit process-environment gate `PYPOST_LIVE_JIRA_SMOKE=1` plus the
protected configuration labels `JIRA_BASE_URL`, `JIRA_CREDENTIALS`, and
`JIRA_PROJECT_KEY`.

This is not routine MCP integration coverage: normal local tests and push/PR
CI remain offline and do not receive Jira configuration. An absent opt-in is a
successful intentional skip. In contrast, an explicitly enabled run with
missing, placeholder, malformed, or non-HTTPS configuration fails without
revealing values. The smoke permits exactly four read-only tools: current-user
lookup, bounded JQL issue search, retrieval of the returned issue, and board
listing.

The protected CI entry is dispatch-only on `master`, under GitHub Environment
`jira-live-smoke`; it reports only passed, failed, or intentionally skipped.
Do not place protected values in commands, files, logs, docs, artifacts, or job
summaries. Complete setup, safety, and offline-contract guidance is in
[Optional Live Jira MCP Smoke](jira_mcp_live_smoke.md).

The shipped **CI-safe** curated-collection MCP e2e pack (PYPOST-1053) uses a
controlled loopback HTTP stand-in for the same four workflows and is part of
the standard fast suite. Run it with `make test-mcp-collection-e2e`; see
[CI-safe Jira MCP Collection E2E](jira_mcp_collection_e2e.md).

### Endpoint environment binding (PYPOST-1044)

Each registry endpoint binds MCP variable resolution to its configured
`environment_id`, not to the environment currently selected in the top bar.
The registry passes copies of variables and hidden keys to that endpoint's
manager. Editing an environment refreshes only rows that selected its ID;
switching the UI selection does not affect MCP clients.

| User action | Effect on connected agents |
| --- | --- |
| Switch top-bar environment | No effect on configured MCP endpoints. |
| Edit an endpoint's selected environment | Matching endpoints receive replacement snapshots; other endpoints keep theirs. |
| Delete a selected collection or environment | The matching endpoint stops and becomes `failed`; peers stay available. |
| Edit a running endpoint row | A replacement must bind before the persisted configuration changes; a failed replacement retains the previous endpoint. |

The legacy `mcp_active_env_changes_total` metric continues to represent
top-bar selection changes for compatibility; it is not a signal that a
registry endpoint changed credentials. Per-endpoint lifecycle is captured by
the aggregate `mcp_server_instances{state}` metric.

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

#### History asymmetry (product choice, PYPOST-701)

Inbound MCP tool calls **do not** append to persistent request history. This is an accepted
product choice, not a defect (audit R-P3-003 / S-HIST-004).

| Entry point | `history_manager` on `RequestService` | Persistent history |
| --- | --- | --- |
| GUI send (`RequestWorker`) | Injected from composition root | Yes — masked entries via `HistoryManager` |
| Inbound MCP (`call_tool`) | Omitted in `_create_request_service()` | No |

**Why:** Inbound MCP uses a fresh, isolated `RequestService` per invocation (PYPOST-138) for
thread safety and session isolation. GUI history is operator-centric (replay, compare, audit
from the UI). Agent-driven tool calls are already surfaced in the session **MCP activity log**
(PYPOST-141), which is separate from the on-disk history file.

**Revisit when:** External agents need masked, persistent audit-trail parity with GUI sends.
Until then, do not wire `history_manager` into `_create_request_service()` without an explicit
product decision. See [Request Execution](request_execution.md#history-recording-by-entry-point).

#### Observability

DEBUG log in `_build_execution_variables`: `mcp_execution_variables_merged` with
`env_var_count`, `hidden_key_count`, `mcp_arg_count` (post-defaulting count; raw count = `mcp_arg_count - defaults_applied_count`),
and `defaults_applied_count` (no names or values; PYPOST-1090). See
`ai-tasks/PYPOST-554/50-observability.md` and `doc/dev/mcp_secrets_policy.md`.

## Threading Model

*   **Main Thread (Qt)**: UI, Dialogs, Settings.
*   **Worker Thread (`RequestWorker`)**: Used for GUI-initiated requests.
*   **MCP Thread (`MCPServerManager`)**: Runs the `uvicorn` loop.
    *   **Thread Pool**: Used inside MCP Thread for blocking I/O (Request execution).
    *   **Variable supplier**: Must not call Qt APIs. For registry-owned endpoints,
        `MCPServerRegistry` installs copied configuration-environment snapshots; the
        `EnvPresenter` cache is used only by the legacy single-manager adapter.
*   **Metrics Thread (`MetricsServer` via `MetricsManager`)**: Runs its own isolated
    `uvicorn` loop for metrics and observability. Bind failures emit `start_failed(str)` on
    `MetricsManager` (PYPOST-153) with the same message style as MCP. `MainWindow` connects
    via `connect_start_failed` so failures during early startup are replayed. Success is logged
    as `metrics_server_listening`, not when the thread starts.

## API / Usage

### `MCPServerManager.set_variable_supplier(supplier)`

Register a callable returning a copy of variables for one endpoint. The registry creates
this supplier from the configuration's environment snapshot before starting that endpoint.
The legacy `EnvPresenter` also wires a supplier for compatibility-only single-manager paths.
Pass `None` to reset to an empty dict.

### `MCPServerManager.set_hidden_keys_supplier(supplier)`

Register a callable returning one endpoint's `hidden_keys` snapshot. The registry sets it
from the configuration's selected environment before start. It is used by `McpSecretsPolicy`
during `list_tools` schema generation.

### `MCPServerImpl._build_execution_variables(mcp_args, env_vars, hidden_keys, request_data=None)`

Internal. Fills omitted/`None` `mcp_args` entries from `request_data.mcp_params[*].default`
when `request_data` is supplied (PYPOST-1054; see
[Optional MCP parameter defaults](#optional-mcp-parameter-defaults-pypost-1054)), logs merge
and defaulting counts at DEBUG (INFO per defaulted param), and returns the merged dict for
`RequestService.execute()`.

### `_merge_execution_variables(env_vars, mcp_args)`

Pure merge helper; unit-tested independently. Spread env vars first, then set `"mcp"` from tool
arguments.

### `format_structured_tool_result(result)`

Public helper. Serializes `ExecutionResult` to the JSON envelope documented above.

### `_tool_result_has_error(result)`

Internal. Returns `true` when `execution_error` is set or `response.status_code == 0`.

## Configuration

`AppSettings.mcp_servers` persists `McpServerConfiguration` rows, with stable `id`, optional
`name`, `host`, `port`, `collection_id`, `environment_id`, and `enabled`. Ports are globally
unique across rows. The legacy `mcp_host`, `mcp_port`, and `Environment.enable_mcp` values are
only explicit migration inputs; see [Multiple MCP Servers](mcp_server_registry.md).

### Collection exposure model (PYPOST-711)

MCP tool registration is **per configured collection**. Each endpoint exposes only
`expose_as_mcp=True` requests from its `collection_id`; it does not aggregate all loaded
collections. Operators control exposure by selecting the correct collection for a row,
unchecking **Expose as MCP** on requests, and stopping/removing an endpoint when it is no
longer needed. The **Tools…** action in MCP Servers shows the selected row's collection only.

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
| MCP tool URL still has `{{ base_url }}` unresolved | Selected endpoint environment has no value, or supplier was not installed | Verify the row's environment and registry start wiring |
| Stale env values after editing variables | The row did not select the edited environment | Refresh/reopen the row and verify its `environment_id`; only matching rows refresh |
| Agent sees different hosts/auth mid-session | Endpoint was reconfigured or the client uses a different endpoint URL | Inspect the named row; top-bar environment switching is not the cause |
| `{{ mcp.request.x }}` works but env vars do not | Custom endpoint setup without supplier | Set both suppliers before `start_server`, or use registry startup |
| Env var named `mcp` ignored for nested keys | By design — merge preserves `mcp.request.*` | Rename the environment variable |
| DEBUG shows `env_var_count=0` | Endpoint's selected environment is empty | Expected when its configured environment has no values; only MCP args resolve |
| Agent cannot connect | Row is stopped, failed, or client uses the wrong host/port | Inspect the row-specific status/error in MCP Servers |
| Port busy on MCP start | Another process or configured row owns the port | Choose a globally unique endpoint port; a failed row does not stop peers |
| Port busy on metrics start | Another process on `metrics_port` (default 9080) | Dialog on main window open; free port or change Settings |
| Optional MCP param stays `None`/missing in the template despite a declared `default` | `default` was set on the wrong parameter name, or `request_data` was not passed into `_build_execution_variables` (e.g. a custom caller bypassing `_execute_request_sync`) | Confirm the param key matches the template's `mcp.request.<name>`, and that `_build_execution_variables` is invoked with `request_data=` set (PYPOST-1054) |
| No `mcp_param_default_applied` log line for a param you expect to default | Caller passed an explicit non-`None` value, or the param's `default` is `None` (undeclared) | Explicit values always win; add a non-`None` `default` in `mcp_params` to enable defaulting |

### Tool metadata authoring (PYPOST-553)

#### Model

| Field | Type | Notes |
| --- | --- | --- |
| `mcp_description` | `str` | Shown in `list_tools`; empty → `name` |
| `mcp_params` | `Dict[str, McpToolParam]` | Keyed by parameter name |

`McpToolParam`: `type` (`string`, `integer`, `number`, `boolean`, `array`, `object`,
`integer_or_string`), `description`, `required` (default `True`), `default`
(`Optional[Any]`, default `None` — PYPOST-1054; see
[Optional MCP parameter defaults](#optional-mcp-parameter-defaults-pypost-1054)).
`default` is validated against `type` at construction time — see
[Default value type validation](#default-value-type-validation-pypost-1089) below.

#### Schema pipeline

```
McpSecretsPolicy.extract_mcp_request_variables(req)  ← regex on mcp.request.VAR (bare & wrapped)
        │
        ▼
resolve_mcp_param_specs(req, discovered)  ← merges mcp_params overrides
        │
        ▼
McpSecretsPolicy.filter_agent_param_specs(...)  ← drops env-only / hidden keys
        │
        ▼
build_tool_input_schema(specs)  → Tool.inputSchema
                                   (publishes "default": spec.default when set, PYPOST-1054)
```

#### UI

`RequestWidget` **MCP** tab: tool description (`QPlainTextEdit`) and `McpParamsTable`
(name, type, description, required, default). Persisted via `_PERSISTED_FIELD_NAMES` in
`request_persisted_fields.py`.

`McpParamsTable` (`pypost/ui/widgets/request_editor.py`) is a 5-column `QTableWidget`:
**Name**, **Type** (a `QComboBox` per row, one of `McpParamsTable._TYPE_OPTIONS` — the
same seven types `_MCP_PARAM_TYPES` accepts in `models.py`), **Description**,
**Required** (checkbox item), and **Default** (PYPOST-1089) — a plain-text cell holding
the default's editable string representation.

##### Default column: rename-safe by construction

Before PYPOST-1089, a parameter's `default` was preserved only via a name-keyed side
dict (`self._defaults`), so renaming a param's **Name** cell silently dropped its
default — the cache's lookup key changed but the cache itself did not track the rename.
The Default column removes that side dict entirely: `_set_row(row, name, spec)` writes
`spec.default`'s string form directly into column 4 of that same row
(`self.setItem(row, 4, QTableWidgetItem(default_text))`), and `get_data()` reads it back
from the same row it reads the (possibly just-renamed) Name cell from. Because the
default now lives in the row, not in a dict keyed by the old name, renaming a param no
longer has any effect on its default — there is no separate key to go stale.

##### `_COERCERS`: type-aware string ↔ value coercion

Round-tripping a typed Python value through an editable text cell needs two directions:

*   **Value → string** (`_serialise_default(value)`, used by `_set_row` when populating
    a row): `None` → `""`; `bool` → `"true"` / `"false"` (checked *before* the general
    numeric/string case, since `bool` is an `int` subclass); `list` / `dict` → compact
    `json.dumps(value, separators=(",", ":"))`; everything else → `str(value)`.
*   **String → value** (`_parse_default(raw, param_type)`, used by `get_data()`): an
    empty (post-`strip()`) cell always yields `None`. Otherwise it dispatches through
    `_COERCERS`, a `dict[str, Callable[[str], Any]]` keyed by MCP param type — a
    strategy-style lookup rather than an `if`/`elif` chain, so adding a coercer for a new
    type is a one-line dict entry:

    | `type` | Coercer | Behavior |
    | --- | --- | --- |
    | `string` | `_coerce_default_string` | Identity — returns the (already-stripped) text |
    | `integer` | `_coerce_default_integer` | `int(raw)` |
    | `number` | `_coerce_default_number` | `int(raw)` when `raw` has no `"."`, else `float(raw)` |
    | `integer_or_string` | `_coerce_default_integer_or_string` | `int(raw)`, falling back to the raw string on `ValueError` |
    | `boolean` | `_coerce_default_boolean` | `raw.lower() in ("true", "1")` |
    | `array` | `_coerce_default_array` | `json.loads(raw)`, requiring the result to be a `list` |
    | `object` | `_coerce_default_object` | `json.loads(raw)`, requiring the result to be a `dict` |

    A coercer that raises `ValueError`, `TypeError`, or `json.JSONDecodeError` is caught
    by `_parse_default`, which logs `mcp_param_default_coerce_failed value=%r
    param_type=%s` at DEBUG and returns `None` — an unparsable Default cell silently
    becomes "no default" rather than raising into `get_data()`'s caller. A type with no
    `_COERCERS` entry falls back to the raw stripped string (matching `string`'s
    behavior).

    Because `get_data()` only ever passes a `_COERCERS` output (or `None`) into
    `McpToolParam(...)`, the table can never itself trigger the
    [default value type validation](#default-value-type-validation-pypost-1089)
    `ValueError` — every value it constructs is already type-matched.

**Known limitations** (see `ai-tasks/PYPOST-1089/60-tech-debt.md` for the full
analysis):

*   **Scientific notation silently drops the default.** `_coerce_default_number`
    disambiguates int vs. float by checking for a literal `"."` in the text, not by
    attempting numeric parsing. `1e-10` or `5e+20` have no `"."`, so `int("1e-10")`
    raises and the default falls back to `None` with only a DEBUG log — no error is
    shown to the user. Normal-range floats (`3.14`, `0.0001`) round-trip correctly.
    Tracked as [PYPOST-1095](https://pypost.atlassian.net/browse/PYPOST-1095).
*   **Unrecognized boolean text silently becomes `False`, not `None`.**
    `_coerce_default_boolean` never raises — `raw.lower() in ("true", "1")` maps *any*
    other text (`"yes"`, `"maybe"`, a typo) to `False`, unlike the other six `_COERCERS`
    entries, which raise on bad input and fall back to `None` via `_parse_default`'s
    `except` clause. Tracked as
    [PYPOST-1096](https://pypost.atlassian.net/browse/PYPOST-1096).
*   The Default cell is plain text for every type — no checkbox for `boolean`, no JSON
    editor for `array`/`object`, and changing the Type combo does not clear or
    re-validate a stale Default cell. Tracked as
    [PYPOST-1099](https://pypost.atlassian.net/browse/PYPOST-1099).

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
*   **`McpToolParam.default` is now type-checked against `type`** (PYPOST-1054 →
    PYPOST-1089 closes the original gap): a param declared `type="boolean"` with
    `default="fifty"` raises `ValidationError` at construction instead of constructing
    silently — see
    [Default value type validation](#default-value-type-validation-pypost-1089). The
    remaining gap is that MCP arguments a *caller* supplies at execution time are still
    unchecked against the declared type, only the declared `default` is — tracked as
    [PYPOST-1100](https://pypost.atlassian.net/browse/PYPOST-1100).
*   **UI now has an affordance to author `default`** (PYPOST-1089): `McpParamsTable`'s
    **Default** column is editable and rename-safe (the default lives in the row, not a
    name-keyed side dict — see [UI](#ui)). Remaining UI gaps: the column is plain text
    for every type (no checkbox for `boolean`, no JSON editor for `array`/`object`,
    [PYPOST-1099](https://pypost.atlassian.net/browse/PYPOST-1099)), and its `_COERCERS`
    dispatch has two known edge cases — scientific-notation numbers
    ([PYPOST-1095](https://pypost.atlassian.net/browse/PYPOST-1095)) and unrecognized
    boolean text silently becoming `False`
    ([PYPOST-1096](https://pypost.atlassian.net/browse/PYPOST-1096)).
*   **`jira-search-assignable-users` pagination**: now exposes optional `maxResults` and
    `startAt` params with defaults (50, 0) matching the other list endpoints (PYPOST-1091).

See `ai-tasks/PYPOST-20/40-tech-debt.md` for more details.

---

## Planned: MCP client tab mode (PYPOST-1164)

Research story [PYPOST-1164](https://pypost.atlassian.net/browse/PYPOST-1164) (Epic
[PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155)) specifies a dedicated **MCP
Client** workspace editor as the third `TabProtocol` peer to HTTP `RequestTab` and
`WebSocketTab`. Users choose **HTTP Request** | **WebSocket** | **MCP Client** from the
blank-tab protocol picker. WS-TM-1 ([PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157))
shipped `Ctrl+N` and tab-bar **+**; MCP-TM-1
([PYPOST-1165](https://pypost.atlassian.net/browse/PYPOST-1165)) added the **MCP Client**
item (`TabProtocol.MCP_CLIENT` / `mcp_client`, stub `McpClientTab`). MCP-TM-2
([PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166)) filled that tab with
draft chrome. Close-last-tab picker reuse is
[PYPOST-1159](https://pypost.atlassian.net/browse/PYPOST-1159). See
[new_tab_protocol_picker.md](new_tab_protocol_picker.md) and
[mcp_client_draft_tab.md](mcp_client_draft_tab.md). Remaining stories add live
`list_tools` / `call_tool` — not via the HTTP request method dropdown.

**Architecture:** [`ai-tasks/PYPOST-1164/20-architecture.md`](../../ai-tasks/PYPOST-1164/20-architecture.md)
— Option A (extend `NewTabProtocolPicker` with a third menu item;
[PYPOST-1165](https://pypost.atlassian.net/browse/PYPOST-1165)),
`TabProtocol.MCP_CLIENT`, `McpClientConnection` / `McpClientTab` / `McpClientPresenter`,
convert-on-open migration for legacy `method: "MCP"` collection items, and retirement of the
HTTP method **MCP** path.

**Implementation stories:**

| Story | Jira | Summary |
| --- | --- | --- |
| MCP-TM-1 (shipped) | [PYPOST-1165](https://pypost.atlassian.net/browse/PYPOST-1165) | Extend protocol picker with **MCP Client** (stub tab; metrics `protocol=mcp_client`) |
| MCP-TM-2 (shipped) | [PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166) | Blank MCP Client draft tab shell |
| MCP-TM-3 | [PYPOST-1169](https://pypost.atlassian.net/browse/PYPOST-1169) | Tool discovery (`list_tools`) and browser UI |
| MCP-TM-4 | [PYPOST-1170](https://pypost.atlassian.net/browse/PYPOST-1170) | Interactive `call_tool` + response pane |
| MCP-TM-5 (shipped) | [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167) | Outbound headers + environment templating |
| MCP-TM-6 | [PYPOST-1171](https://pypost.atlassian.net/browse/PYPOST-1171) | Migrate/remove HTTP method **MCP** |
| MCP-TM-7 | [PYPOST-1172](https://pypost.atlassian.net/browse/PYPOST-1172) | Collections save/open + context menu parity |
| MCP-TM-8 | [PYPOST-1168](https://pypost.atlassian.net/browse/PYPOST-1168) | User documentation alignment |

**Current state (until MCP-TM-3 … MCP-TM-8 land):**

*   `Ctrl+N` / **+** include **MCP Client**; confirm opens a draft `McpClientTab` (not HTTP)
    with URL, Headers table, Connect / Disconnect, disconnected state, and an empty
    tool browser. Connect is local chrome (no `MCPClientService`). See
    [mcp_client_draft_tab.md](mcp_client_draft_tab.md).
*   Outbound MCP operations in the GUI are still only available as HTTP method **MCP** on
    `RequestEditor` — raw JSON body conventions for `list_tools` / `call_tool`, not a
    dedicated editor. The draft tab's header-aware seam is
    `McpClientPresenter.execute_outbound` (MCP-TM-3 / TM-4 must call it).
*   `RequestService._execute_mcp` renders URL and headers from templates and passes the
    URL plus resolved headers to `MCPClientService.run` (PYPOST-1173). Those headers
    reach `create_mcp_http_client` on the existing method-MCP path. MCP-TM-5
    (PYPOST-1167) shipped the same resolve + `headers=` contract on the MCP Client
    presenter (`TemplateService.render_string`; empty table → `headers={}`).
*   Inbound surfaces are **unchanged** by this epic: **MCP Servers…**, **Expose as MCP Tool** /
    **MCP Tool** checkbox, and the HTTP editor **MCP** sub-tab for inbound tool exposure remain
    as documented above. See also [MCP Reverse Proxy](mcp_proxy.md) for inbound bridge mode.

Until MCP-TM-3 … MCP-TM-8 land, **`method: "MCP"` requests** (e.g. `examples/collections/mcp.json`)
remain the only **operational** outbound MCP path in the GUI (the draft tab Connect does not
talk to a server). Inbound MCP server tooling is unchanged.
