# Architecture: PYPOST-1044 — Launch multiple independent MCP servers

## Decision

Replace the application-wide, mutable single-server lifecycle with a registry
of independently configured server instances.  A server configuration is
identified by a stable instance ID and stores the selected collection ID,
environment ID, bind host, and port.  At runtime that configuration owns one
dedicated `MCPServerManager`/`MCPServerImpl` pair, including its own tool map,
environment and hidden-key snapshot suppliers, activity log, server thread,
and lifecycle state.

This is intentionally composition over a shared `MCPServerImpl`: sharing an
implementation or the active environment supplier would allow a subsequent UI
selection to change another endpoint's credentials or tool exposure.

## Research

The current implementation establishes these relevant constraints:

- `pypost.core.qt.mcp_server.MCPServerManager.start_server()` calls
  `stop_server()` when its one thread is already running, and `update_tools()`
  also stops/restarts that same endpoint. It is therefore a correct
  single-instance primitive but cannot be the application-wide lifecycle
  owner for several endpoints.
- Each `MCPServerManager` creates one `MCPServerImpl`, one `McpActivityLog`,
  a `uvicorn.Server`, and an explicit background thread. Its `start_failed`
  signal already carries a clear bind failure suitable for routing by a new
  instance ID.
- `pypost.core.mcp_server_impl.MCPServerImpl` owns the tool map and invokes
  the variable and hidden-key suppliers at call time. Its per-impl request
  execution and streamable HTTP/SSE routes can remain unchanged when each
  endpoint receives a distinct implementation.
- `pypost.ui.presenters.env_presenter.EnvPresenter._on_env_changed()` starts
  or stops the singleton based on the active environment and gives it an
  `EnvVariableSnapshot`. `_get_mcp_tools()` aggregates tools from all loaded
  collections. Both global sources must be removed from endpoint execution.
- `pypost.models.settings.AppSettings` has only one `mcp_host`/`mcp_port`,
  and `Environment.enable_mcp` is the legacy toggle; persisted server
  configurations are needed for an independently manageable list.
- Existing manager and integration tests provide `free_port`, `wait_for_port`,
  and live streamable-HTTP clients. They support deterministic concurrent
  endpoint and bind-failure regression tests without fixed ports.

## Current state and boundary

`EnvPresenter` currently reacts to the one global environment selector by
starting/stopping the one injected `MCPServerManager`; the manager restarts
itself when its tool signature changes.  Its `MCPServerImpl` gets variables
from an `EnvVariableSnapshot` tied to that global selection, and tools come
from every loaded collection.  That arrangement has no identity with which to
address more than one endpoint and cannot provide collection/environment
isolation.

Keep `MCPServerImpl` as the per-endpoint HTTP/MCP implementation.  Introduce a
higher-level runtime owner (named `MCPServerRegistry` below) instead of adding
another mode to its single-server API.

## Data model and persistence

Add an `McpServerConfiguration` Pydantic model to `pypost.models.settings`:

| Field | Purpose |
| --- | --- |
| `id` | Stable instance identity used by UI and runtime registry. |
| `name` | User-visible optional label; fall back to collection/environment/port summary. |
| `host`, `port` | Per-server bind endpoint. |
| `collection_id` | Exactly one selected persisted collection. |
| `environment_id` | Exactly one selected persisted environment. |
| `enabled` | Whether this persisted instance should auto-start at application/session startup. |

Add `mcp_servers: list[McpServerConfiguration]` to `AppSettings`, defaulting
to an empty list, so existing settings remain valid. Validate ports using the
existing bind-address validation rules and reject a duplicate **port** across
all configured instances before any launch attempt, irrespective of host. A
registry port reservation also prevents a concurrent Start action from using
the same port. Retain the existing `mcp_host`,
`mcp_port`, and `Environment.enable_mcp` fields only as legacy input during
this task; do not use them as mutable inputs to new server instances.

For backward compatibility, an existing user whose selected environment has
`enable_mcp=True` continues to see the familiar single “default MCP server”
path.  On first use of the server manager, the UI presents a one-time
conversion: select one collection plus that environment and create the default
configuration using the legacy bind host/port.  The legacy environment toggle
does not automatically start a new multi-server instance after conversion.
This avoids silently exposing all collections on a server that must be bound
to one selected collection, while leaving a clear migration path.

At application/session startup the registry loads settings and starts each
`enabled=True` configuration after collections and environments are available;
`enabled=False` rows remain stopped until the user selects Start. Startup is
best-effort per instance: one missing reference or bind failure marks only
that row as failed/stopped and never prevents another enabled instance from
starting. Start and Stop update `enabled` and persist settings, making the
next session's behavior explicit rather than depending on an in-memory global
selection.

## Runtime ownership and isolation

`MCPServerRegistry` receives the common metrics and `TemplateService`, plus
read-only collection/environment lookup functions.  It owns
`dict[str, ManagedMcpServer]`, where a managed value contains:

```
McpServerConfiguration
  └─ ManagedMcpServer
       ├─ MCPServerManager (one thread, one MCPServerImpl, one activity log)
       ├─ immutable/deep-copied selected collection requests
       └─ EnvVariableSnapshot copied from the selected environment
```

At `start(id)`, the registry resolves the configured collection and
environment by ID.  If either no longer exists, it fails just that instance
with a clear, instance-labelled message and never starts with a fallback
global selection.  It deep-copies the selected collection requests before
registering them, initializes that instance's variable/hidden-key snapshot
from the selected environment, and starts only that manager at its configured
host/port.  The manager's existing bind failure path is surfaced with the
instance label and port; a failed bind removes/marks only the attempted
runtime value, leaving all existing managers untouched.

`stop(id)`, `restart(id)`, and `remove(id)` act solely on the matching
manager. `stop_all()` is used only on application and agent-session shutdown.
`is_running(id)` and `list_statuses()` return per-instance state.  Registry
signals include the instance ID, so the UI never mistakes server A's startup
failure or activity for server B's.

When a collection changes, `refresh_collection(collection_id)` refreshes only
servers selected for that collection.  It snapshots that collection again and
calls only each matching manager's tool update/restart operation.  When an
environment changes, `refresh_environment(environment_id)` updates only the
matching instances' snapshots.  Environment snapshots are copied under the
registry/UI thread boundary; no server reads the global environment selector.
Changing a server's configuration is a transaction: validate IDs and port,
stop only that instance if it is running, replace its owned runtime value, and
start it.  If replacement cannot bind, report its failure and leave other
servers alive; the UI keeps the prior configuration/state available for a
user retry rather than mutating another server.

Metrics remain shared aggregation, but activity histories stay per instance.
Metric labels must not contain collection names, environment names, raw
variables, or credentials; instance ID/port is available in structured logs
only if the existing observability policy permits it.

## UI and lifecycle

Add an **MCP Servers** management dialog/panel reachable from the existing MCP
status area.  It lists one row per configuration with label, state, endpoint,
collection name, and environment name.  Its controls are Add, Edit, Start,
Stop, Remove, and per-instance Activity.  The add/edit dialog requires a
collection and environment selection and a valid port before enabling Start.
Its port-conflict message identifies the attempted server and says already
running servers were not changed.

The environment selector remains the context for normal request editing; it
no longer starts/stops or reconfigures all MCP endpoints.  The existing
single MCP status label is replaced by a summary (for example, “MCP Servers:
2 running”) and opens the manager.  The existing MCP tools overview becomes
per selected server, derived from that server’s collection.

`compose_app` constructs the registry and passes it to `MainWindow`/the
presenter instead of a singleton `MCPServerManager`.  Both `main()` and
`AgentAppSession.shutdown()` call `registry.stop_all()`.  The resulting
`ComposedApp` exposes the registry; update tests/callers that currently refer
to `mcp_manager` in the same change to preserve a single explicit shutdown
owner.

## Failure handling

| Condition | Result |
| --- | --- |
| Duplicate configured port | Dialog validation rejects the edit before launch, regardless of host. |
| OS port already busy | Only the attempted manager emits failure/Stopped; all others remain running. |
| Collection/environment deleted | Affected instance displays Missing collection/environment and cannot start; no fallback selection. |
| Collection edited | Only servers selecting it refresh; unrelated endpoints and ports are untouched. |
| Environment variable/hidden-key edit | Only servers selecting it receive a new snapshot. |
| Shutdown | `stop_all()` cleanly stops every registered manager. |

## Step 3 red-test plan

Create focused tests before implementation; do not alter current behavior in
this step.

1. `tests/test_mcp_server_registry.py`: start two configurations on distinct
   free ports with distinct single-tool collections and environments; list
   tools from each streamable HTTP endpoint and assert each gets only its own
   tool.  Invoke both tools through a mocked request service and assert each
   receives only its selected environment variables.
2. Same test module: stop/reconfigure server A and assert server B remains
   listening, its tool list and variable snapshot are unchanged, and its
   manager identity is unchanged.
3. Same module: occupy one requested port, start A successfully, then attempt
   B on the occupied port; assert B reports its own bind failure while A stays
   running and callable.
4. `tests/test_mcp_servers_presenter.py` (or the new dialog test module):
   validate required collection/environment, duplicate endpoint prevention,
   row identity/state, and that UI actions are routed by server ID.
5. Extend settings/config serialization tests for empty legacy configurations,
   persisted multiple configurations, enabled auto-start/disabled stopped
   behavior, partial enabled-startup failure while another server remains
   available, and the explicit one-time legacy conversion path.
6. Update existing `tests/test_mcp_server_manager.py` only to retain the
   single-instance contract; it remains the low-level lifecycle test suite.

No test may rely on the active environment selector for an endpoint's request
variables.  Use `free_port`, `wait_for_port`, and the existing MCP client
helpers to avoid fixed-port concurrency flakes.

## Non-goals

This design does not change collection request definitions, environment
secrets, MCP tool contracts, inbound authentication, external client setup, or
metrics-server lifecycle.  It also does not introduce sharing between server
instances: equal configuration values still create independent endpoints.

## Q&A

| Question | Decision |
| --- | --- |
| Are ports unique only per bind host? | No. A port is the endpoint identity in the requirements; reject and reserve it globally across all configured/running PyPost MCP instances. |
| Do configured servers survive restart? | Yes. Configurations persist in `AppSettings`; `enabled=True` auto-starts only after collection/environment loading completes. |
| Can an enabled server's failed startup block application launch or another server? | No. Startup is independent and failure is reported on the affected row only. |
| Does changing the normal active UI environment retarget a server? | No. An endpoint resolves only its configured environment ID and owns a copied snapshot. |
| Do collection/environment edits refresh every server? | No. Refresh only instances whose configured collection/environment ID matches the changed record. |
| What is the existing one-server migration? | A guided, explicit first-use conversion creates a default configuration after the user selects a single collection, instead of silently retaining the old all-collections behavior. |

## Review checklist

- [x] Every endpoint owns its tool map, environment snapshot, hidden keys,
  lifecycle manager, activity log, and port.
- [x] Port-bind failure cannot call a global stop/restart operation.
- [x] Collection and environment lookup uses stable persisted IDs, not UI
  indices or mutable active selection.
- [x] Existing users have an explicit understandable migration path instead
  of an implicit all-collections multi-server endpoint.
- [x] Step 3 covers concurrent availability, catalog/context isolation,
  lifecycle isolation, and port-conflict survival.

## STEP 2 approval basis

An independent architecture reviewer required corrections for global port
uniqueness, explicit Research/Q&A, and enabled auto-start semantics. After
those corrections, the reviewer passed this architecture. The approval record
is also retained in the roadmap.
