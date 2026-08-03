# MCP Integration (Developer Guide)

See also [PyPost MCP Integration](../mcp_integration.md) for user-facing setup, client
configuration (Cursor, Claude Desktop), and operator troubleshooting.

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
    `McpToolParam` records (`type`, `description`, `required`).
*   **Schema Generation**: Discovers `{{ mcp.request.VAR_NAME }}` placeholders in URL,
    headers, params, and body via regex in `McpSecretsPolicy.extract_mcp_request_variables`.
    Merges discovered names with explicit `mcp_params` and builds JSON Schema via
    `build_tool_input_schema`.
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

### 4. `EnvPresenter` (`pypost/ui/presenters/env_presenter.py`)

The environment selector opens the registry-backed MCP Servers dialog and
continues to own the legacy single-server adapter used in focused compatibility
tests. It no longer owns lifecycle or variable context for persisted
multi-server endpoints.

*   **Responsibility**: Load environments, emit variable changes to the UI, and route
    endpoint management to the registry-backed MCP Servers dialog.
*   **Variable cache**: `EnvVariableSnapshot` is updated on the main thread in
    `_on_env_changed` whenever the user selects or edits an environment.
*   **Supplier registration**: On init, calls
    `MCPServerManager.set_variable_supplier(self._env_snapshot.snapshot_variables)`.
    The snapshot returns a **copy** so MCP threadpool workers never observe partial writes.
*   **MCP tools overview**: With a registry, top-bar **MCP Server Tools…** opens
    the MCP Servers dialog; **Tools…** is scoped to the selected row's collection.
*   **MCP activity log**: The registry dialog exposes activity for the selected endpoint.
*   **Status label**: With a registry it shows aggregate running/failed counts, not a
    potentially misleading endpoint. Row-specific state and errors live in the dialog.

### 5. Metrics observability stack (`pypost/core/metrics*.py`)

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

1.  `MainWindow` loads every persisted `AppSettings.mcp_servers` row into
    `MCPServerRegistry`.
2.  After collections and environments are both loaded, `start_enabled()` starts
    each enabled row independently.
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
sorted `McpToolOverviewEntry` rows. `EnvPresenter` opens `McpToolsOverviewDialog` from the
top bar. Overview is read-only and does not require MCP to be running.

### Scoped tool list refresh

When the user saves a request or edits collections while MCP is running, PyPost must expose an
up-to-date tool catalog to connected agents.

1.  `MainWindow` connects collection changes to `EnvPresenter.refresh_mcp_tools()`.
2.  With a registry, the presenter first reconciles missing collection/environment
    references and then calls `refresh_collection(id)` for each current collection.
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
`McpActivityDialog` for the selected endpoint through `MainWindow.mcp_server_activity()`.
The top-bar **MCP Activity (N)** remains the legacy single-manager view and is not an
aggregate registry activity feed.

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
`env_var_count`, `hidden_key_count`, and `mcp_arg_count` (no names or values). See
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
`request_persisted_fields.py`.

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
