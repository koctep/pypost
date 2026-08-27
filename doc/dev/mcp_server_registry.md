# Multiple MCP Servers

## Overview

PYPOST-1044 replaces the application-owned mutable MCP endpoint with persisted,
independent MCP server configurations. Each configuration selects exactly one
collection and one environment, binds to its own port, and owns an independent
runtime. This lets separate MCP clients use different tool catalogs and
credentials at the same time.

The primary developer entry point is `MCPServerRegistry` in
`pypost/core/mcp_server_registry.py`. The legacy `MCPServerManager` remains
the single-endpoint transport primitive used by each registry row; it is no
longer the owner of the application-wide multi-server lifecycle.

## Architecture

`McpServerSettingsController` (`pypost/ui/mcp_server_controller.py`, PYPOST-1071)
constructs the registry with ID-based collection and environment lookups, then
loads persisted rows before asynchronous collection and environment loading
starts. `MainWindow` composes that controller and keeps only the readiness
gate: once both sources are ready it calls `mcp_controller.start_enabled()`,
which starts every row with `enabled=True`. Startup is best-effort: a missing
reference or bind failure marks that row failed and does not interrupt another
endpoint.

For each started row the registry creates one `MCPServerManager`, which in turn
owns one `MCPServerImpl`, activity log, uvicorn server, and background thread.
Before starting it, the registry deep-copies the selected collection requests
and snapshots the selected environment variables and hidden keys. A later
change in the environment selector therefore cannot retarget a running
endpoint.

```text
AppSettings.mcp_servers
        |
        v
MCPServerRegistry -- one runtime per configuration --> MCPServerManager
        |                                            --> MCPServerImpl
        +-- collection/environment ID lookup + copied snapshots
```

`McpControlsPresenter` (`pypost/ui/presenters/mcp_controls_presenter.py`,
PYPOST-1071) owns the **MCP Servers…** entry point; `EnvPresenter` only hosts
its widgets in the environment bar. The top-bar status is an aggregate
running/failed count, while the dialog presents row-specific state, endpoint,
collection, environment, activity, and scoped tool overview.

## Configuration and lifecycle

`AppSettings.mcp_servers` is a list of `McpServerConfiguration` objects saved
to the normal PyPost `settings.json`. A row contains:

| Field | Meaning |
| --- | --- |
| `id` | Stable instance identity used by the registry and UI. |
| `name` | Optional display label. |
| `host`, `port` | Endpoint bind address. Ports must be unique across all rows, even with different hosts. |
| `collection_id` | The only collection whose exposed requests become tools for this endpoint. |
| `environment_id` | The environment snapshot used by this endpoint's tool calls. |
| `enabled` | Starts the row after collections and environments have loaded on the next session; **Start** sets it, **Stop** clears it. |

Use `McpServersDialog` through `McpControlsPresenter` for normal changes. Its
Add and Edit forms validate the selected collection, environment, port range,
and global configured-port uniqueness. `McpServerSettingsController` persists a
non-running edit immediately. For a running endpoint it calls
`MCPServerRegistry.reconfigure()`: the replacement endpoint must start
successfully before its persisted configuration replaces the old one. If it
cannot bind, the old endpoint remains available (or is restarted for a
same-address replacement) and the edit is not persisted.

The registry API is intentionally per-instance:

```python
registry.upsert(configuration)       # validate and store a configuration
registry.start(instance_id)          # start only this endpoint
registry.stop(instance_id)           # stop only this endpoint
registry.reconfigure(instance_id, configuration)
registry.remove(instance_id)
registry.refresh_collection(collection_id)
registry.refresh_environment(environment_id)
registry.stop_all()                  # application/agent-session shutdown only
```

`refresh_collection()` updates only servers selected for that collection;
`MCPServerManager.update_tools()` may restart only those endpoint(s) when the
tool signature changed; the restart path waits until the prior host/port is
probe-bindable before starting again, retaining the worker thread ref if stop’s
join times out (PYPOST-1178 / PYPOST-1196; see
[MCP Integration](mcp_integration.md)). `refresh_environment()` replaces the
variables and hidden-key suppliers only for servers that selected that
environment.
`reconcile_references()` stops and marks only rows whose persisted collection
or environment was deleted.

## Legacy migration

The old `Environment.enable_mcp` plus global `mcp_host` / `mcp_port` setting
is retained only as an explicit migration input. It does not automatically
start a multi-server endpoint. When the selected legacy environment has
`enable_mcp=True`, **MCP Servers…** offers **Convert current legacy MCP
setting…**. The form preselects that environment and the legacy host/port; the
user must select a collection and save a new explicit row. Conversion does not
change the legacy environment toggle.

## Observability

Registry lifecycle logs include only stable operational context:
`instance_id`, `port`, lifecycle state, and whether a message exists. They do
not log collection names, environment values, hidden keys, credentials, or
request payloads. Failed transactional replacements emit a warning with the
attempted port and reason.

The registry covers the endpoint **runtime**; `McpServerSettingsController`
covers **persistence** — `mcp_persisted_servers_loaded` at startup,
`mcp_servers_persist_requested reason=…` before every settings write, and
`mcp_server_reconfigure_finished instance_id=… committed=…` for the
transactional path (`committed=false` means the edit was rolled back and not
persisted). Both sets emit counts and opaque instance IDs only; the full
catalog is in [logging.md](logging.md#mcp).

`mcp_server_instances{state}` is the aggregate count of configured rows in
`stopped`, `starting`, `running`, and `failed` state. The label set is fixed;
instance IDs, ports, collection IDs, and environment IDs are intentionally not
metric labels. The existing `mcp_server_up` compatibility gauge remains true
while at least one registry endpoint is running. Request counters and duration
histograms remain aggregate; inspect the selected dialog row for its activity.

## Troubleshooting

| Symptom | Check / resolution |
| --- | --- |
| A row is `failed` after startup | Verify its selected collection and environment still exist, then resolve the dialog's error and start that row again. Other rows should stay available. |
| Add or edit rejects a port | Each configured row reserves its port globally. Choose a unique port; a running-row reconfiguration also checks whether the OS can bind it. |
| One client sees unexpected tools | Open **MCP Servers…**, select that endpoint, and use **Tools…**. Verify its collection selection and that requests are marked as MCP tools. |
| An edit did not take effect | A running endpoint is persisted only after its replacement binds. Inspect the row state/error; the previous endpoint is retained on replacement failure. |
| Environment changes do not affect a different server | This is expected. A server receives only the snapshot for its configured environment; edit/select that row's environment instead. |

Run the focused checks after changing this subsystem:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q \
  tests/test_mcp_server_registry.py tests/test_mcp_servers_dialog.py
```
