# MCP Process vs Thread Execution Mode (PYPOST-1439)

## Overview

Standalone MCP servers can run in either **thread** mode (default, shared address
space) or **process** mode (OS-isolated workers under a supervisor). Process mode
implements Phase 2 of the
[multi-process supervisor evaluation](mcp_process_supervisor_evaluation.md)
([PYPOST-1439](https://pypost.atlassian.net/browse/PYPOST-1439)).

Thread mode remains the lightweight default and preserves the concurrency contracts
documented in
[Concurrent Multi-Server Lifecycle (PYPOST-1418)](mcp_concurrent_multiserver.md).
Process mode adds crash containment and per-server GIL isolation at the cost of
higher memory and spawn latency.

---

## Architecture

```text
AppSettings.mcp_execution_mode  ("thread" | "process", default "thread")
        │
        ▼
MCPServerRegistry(execution_mode=...)
        │
        ├── thread  → ThreadServerRunner → MCPServerManager (daemon thread + uvicorn)
        └── process → ProcessServerRunner → McpProcessSupervisor
                                              │
                                              └── spawn → mcp_worker_process.worker_main
                                                          (headless; no PySide6)
```

| Component | Module | Role |
| --- | --- | --- |
| Setting | `pypost/models/settings.py` | `mcp_execution_mode`, heartbeat, restart, limits |
| Registry | `pypost/core/mcp_server_registry.py` | Selects runner; routes recovery and exits |
| Runners | `pypost/core/mcp_server_runner.py` | `MCPServerRunnerProtocol`, thread/process runners |
| Supervisor | `pypost/core/mcp_process_supervisor.py` | Process table, IPC, stop, backoff |
| IPC helpers | `pypost/core/mcp_worker_ipc.py` | Versioned envelopes (`v: 1`), tool encode/decode |
| Worker | `pypost/core/mcp_worker_process.py` | Spawn target; uvicorn + local or proxy server |

Host wiring passes the setting into the registry:

- GUI: `pypost/ui/mcp_server_controller.py`
- Daemon: `pypost/core/qt/daemon_runtime.py`

Mode is fixed when the registry is constructed. Changing `mcp_execution_mode` applies
on the **next** registry construction / server start — do not mix runners for the same
`instance_id` while it is running.

---

## Configuration

### `mcp_execution_mode`

| Value | Behavior |
| --- | --- |
| `thread` (default) | In-process daemon threads; live suppliers; cooperative cancel |
| `process` | One OS process per server via spawn; variable snapshots over IPC |

```python
from pypost.models.settings import AppSettings
from pypost.core.mcp_server_registry import MCPServerRegistry

settings = AppSettings(mcp_execution_mode="process")
registry = MCPServerRegistry(execution_mode=settings.mcp_execution_mode)
```

There is not yet a Settings dialog control for this field (tech debt); operators and
tests set it on `AppSettings` / registry construction.

### `mcp_restart_policy` (PYPOST-1466)

Isolated process-mode workers support configurable automatic restart with progressive
exponential backoff via `AppSettings.mcp_restart_policy`:

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `enabled` | `bool` | `False` | Opt-in toggle. Default `False` fails immediately on exit. |
| `max_retries` | `int` | `3` | Maximum consecutive restart attempts (`0` to `100`). |
| `initial_backoff_s` | `float` | `0.5` | Delay in seconds before first restart attempt (`> 0.0`). |
| `max_backoff_s` | `float` | `8.0` | Capped backoff delay (`> 0.0`, `>= initial_backoff_s`). |
| `backoff_multiplier` | `float` | `2.0` | Exponential growth factor applied per retry (`>= 1.0`). |
| `healthy_reset_window_s` | `float` | `30.0` | Uptime in seconds to reset retry count (`>= 0.0`). |

```python
from pypost.models.settings import AppSettings, McpWorkerRestartPolicy
from pypost.core.mcp_server_registry import MCPServerRegistry

policy = McpWorkerRestartPolicy(
    enabled=True,
    max_retries=3,
    initial_backoff_s=0.5,
    max_backoff_s=8.0,
    backoff_multiplier=2.0,
    healthy_reset_window_s=30.0,
)
settings = AppSettings(mcp_execution_mode="process", mcp_restart_policy=policy)
registry = MCPServerRegistry(
    execution_mode=settings.mcp_execution_mode,
    restart_policy=settings.mcp_restart_policy,
)
```

The restart policy defaults to disabled (`enabled=False`), maintaining backwards-compatible
immediate crash containment (where child crashes transition directly to `failed`).

### `mcp_resource_limits` (PYPOST-1469)

Isolated process-mode workers support configurable memory ceilings and spawn admission
control via `AppSettings.mcp_resource_limits`:

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `max_process_workers` | `int` | `0` | Active worker limit (`0` to `100`; `0` is unlimited). |
| `max_total_rss_mb` | `float` | `0.0` | Total RSS budget in MB (`>= 0.0`; `0.0` is unlimited). |
| `soft_memory_limit_mb` | `float` | `0.0` | Warning threshold in MB (`>= 0.0`; `0.0` disabled). |
| `hard_memory_limit_mb` | `float` | `0.0` | Kill threshold in MB (`>= 0.0`; `0.0` disabled). |
| `memory_sample_interval_s` | `float` | `1.0` | Memory sampling interval in seconds (`> 0.0`). |
| `default_worker_rss_estimate_mb` | `float` | `50.0` | Estimated RSS for spawns (`> 0.0`). |

```python
from pypost.models.settings import AppSettings, McpResourceLimitsPolicy
from pypost.core.mcp_server_registry import MCPServerRegistry

limits = McpResourceLimitsPolicy(
    max_process_workers=4,
    max_total_rss_mb=512.0,
    soft_memory_limit_mb=128.0,
    hard_memory_limit_mb=256.0,
    memory_sample_interval_s=1.0,
    default_worker_rss_estimate_mb=50.0,
)
settings = AppSettings(mcp_execution_mode="process", mcp_resource_limits=limits)
registry = MCPServerRegistry(
    execution_mode=settings.mcp_execution_mode,
    resource_limits=settings.mcp_resource_limits,
)
```

Cross-field validation enforces `hard_memory_limit_mb >= soft_memory_limit_mb` whenever both
thresholds are enabled (> 0.0). By default, resource limits are unconstrained (0 / 0.0),
maintaining backward-compatible operation.

### `mcp_heartbeat_policy` (PYPOST-1468)

Isolated process-mode workers support an active heartbeat watchdog to detect event loop freezes,
deadlocks, and unresponsive processes via `AppSettings.mcp_heartbeat_policy`:

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `enabled` | `bool` | `True` | Opt-in watchdog toggle. Default `True` enables probing. |
| `interval_s` | `float` | `2.0` | Heartbeat probe frequency in seconds (`> 0.0`). |
| `timeout_s` | `float` | `5.0` | Probe-to-pong timeout latency in seconds (`> 0.0`). |

```python
from pypost.models.settings import AppSettings, McpHeartbeatPolicy
from pypost.core.mcp_server_registry import MCPServerRegistry

policy = McpHeartbeatPolicy(
    enabled=True,
    interval_s=2.0,
    timeout_s=5.0,
)
settings = AppSettings(mcp_execution_mode="process", mcp_heartbeat_policy=policy)
registry = MCPServerRegistry(
    execution_mode=settings.mcp_execution_mode,
    heartbeat_policy=settings.mcp_heartbeat_policy,
)
```

Cross-field validation enforces `timeout_s >= interval_s > 0.0` to prevent watchdog flapping.
By default, the watchdog is active (`enabled=True`), providing automated freeze detection.


### Environment gates (test / debug only)

| Variable | Effect |
| --- | --- |
| `PYPOST_MCP_ALLOW_DEBUG_IPC=1` | Enables supervisor debug opcodes (`DEBUG_ABORT`, `DEBUG_HANG`). |
| `PYPOST_MCP_TEST_ECHO_VARS=1` | Echoes variable snapshot in response body for isolation tests. |

Neither gate is required for production. Isolation tests set both as needed before spawn.

---

## API / Usage

### `MCPServerRunnerProtocol`

Host-facing lifecycle used by the registry:

- `start(spec: ServerStartSpec) -> None`
- `stop(timeout: float | None = None) -> bool`
- `is_running() -> bool`
- `is_listening() -> bool`
- `last_start_error` → `str | None`
- `update_tools(tools: list[Any]) -> bool`
- `update_variables(variables, hidden_keys, overridable_keys) -> None`

`ServerStartSpec` carries configuration, tools, and the initial variable snapshot
(dict + key sets). Public registry start/stop/status semantics are unchanged
(`stopped` / `starting` / `running` / `failed`).

### `ThreadServerRunner`

Wraps `MCPServerManager`. Variable suppliers remain live `Callable` closures.
`update_tools(tools)` delegates to `MCPServerManager.update_tools(tools)`, which
always refreshes `MCPServerImpl.register_tools(tools)` in place (capturing updated
URLs, methods, descriptions, headers, bodies, and parameter schemas) and restarts
the thread transport only when the exposed `(id, name)` tool signature changes.
Stop uses `CancellationTokenSource` and `adaptive_thread_join` (default ~2.0s).

### `ProcessServerRunner`

Delegates to a shared `McpProcessSupervisor`. Forwards both local tool inputs and
proxy settings (`server_type`, `upstream_url`, `upstream_transport`, copied `headers`,
and `timeout`) from `ServerStartSpec.configuration` to `spawn_worker` (PYPOST-1464).
Converts tool updates into `UPDATE_TOOLS` IPC messages (`update_tools(tools) -> bool`,
PYPOST-1465) and supplier updates into `UPDATE_VARIABLES` IPC snapshots. Exposes
`send_debug_opcode` for tests only. The read-only `worker_id` identifies the supervisor
entry independently of the public configuration ID. `start_snapshot` returns a deep copy
of the accepted start payload (including proxy configuration); both `update_tools` and
`update_variables` refresh the `_spec` snapshot used for reconfiguration rollback recovery
and auto-restart respawn. `is_restarting()` and `retry_count()` reflect transient recovery
progress (PYPOST-1466).

### Live collection tool and variable refresh (PYPOST-1465)

Calling `registry.refresh_collection(collection_id)` updates all local servers bound to
`collection_id`—both workspace-backed (`configuration.collection_id == collection_id`) and
library-backed (`configuration.library_id` with matching `library_collection_path`, stem,
or filename)—while skipping proxy servers (`server_type == "proxy"`) and unrelated peers:

1. **Resolution & Variable Merging**:
   - **Library-backed rows**: Re-resolve `(tools, variables, hidden_keys, overridable_keys)`
     via `_runtime_inputs(configuration)` (`LibraryRuntimeResolver` 3-tier merge: collection
     defaults < active environment < local overlay).
   - **Workspace-backed rows**: Copy `collection.requests` and merge collection variable
     defaults (`Collection.variables`) beneath the active environment's variables via
     `_merge_workspace_variables(collection, env)` while merging secret collection variable
     names (`v.secret=True`) into `hidden_keys` and preserving `environment.mcp_overridable_keys`.
   - If the target collection or library reference no longer resolves, only that instance
     transitions to `failed` without affecting peers.
2. **Process-mode zero-downtime update**:
   - `ProcessServerRunner.update_tools(tools)` calls
     `McpProcessSupervisor.update_tools(instance_id, tools) -> bool`, which verifies the
     worker is running/alive and sends `make_message("UPDATE_TOOLS", tools=encode_tools(tools))`
     over the parent control pipe (catching broken-pipe/serialization errors and returning
     `False` instead of raising).
   - In `mcp_worker_process.worker_main`, the worker decodes the tools via `decode_tools`,
     invokes `MCPServerImpl.register_tools(tools)` (which atomically replaces `self.tools_map`
     with a freshly constructed dict so concurrent `list_tools` / `call_tool` coroutines never
     observe a partially cleared map), and replies with `ACK(correlating="UPDATE_TOOLS")`.
     Registered entries keep the caller-supplied object identity (no second `model_copy` inside
     `register_tools`); isolation copies remain at registry refresh and IPC decode boundaries
     (PYPOST-1535).
   - When collection or environment variables are present, `runner.update_variables(...)`
     follows with `UPDATE_VARIABLES`. Both updates preserve the existing worker PID and
     listening socket with zero downtime and synchronize `runner._spec` (`start_snapshot`).
   - If a process worker has exited or fails IPC dispatch during `refresh_collection`,
     the registry logs `mcp_registry_refresh_collection_worker_failed` (or
     `mcp_registry_refresh_collection_variables_failed`), marks only that instance `failed`,
     and continues refreshing remaining healthy servers.
3. **Thread-mode parity**:
   - Updates variable/hidden/overridable suppliers on `MCPServerManager` and calls
     `manager.update_tools(tools)`, refreshing `MCPServerImpl.register_tools(tools)` in place
     even when tool IDs/names are unchanged.

### Live process reconfiguration (PYPOST-1463)

Call `registry.reconfigure(instance_id, replacement)` with the same configuration ID.
Existing identity, reference, and port validation runs before disturbing the accepted
worker. A stopped instance accepts the configuration for its next start. A running
process instance uses a bounded supervised replacement transaction:

1. Create a candidate runner with a unique internal worker ID on the shared supervisor.
2. If the endpoint changes, keep the old worker serving until the candidate acknowledges
   startup. If the endpoint stays the same, reclaim the old worker before candidate startup;
   clients of that endpoint may briefly disconnect.
3. Confirm candidate liveness and reclaim the prior worker before publishing the replacement
   configuration and runner together. Emit `reconfiguration_finished(instance_id, True)`.
4. On rejection, reclaim the candidate and retain the prior worker when still running.
   Otherwise make one bounded restart attempt from the copied accepted runtime snapshot.
   Emit `reconfiguration_finished(instance_id, False)` and retain the prior configuration.

Recovery restores the accepted tools, variables, and hidden/overridable key sets rather
than resolving possibly changed library or environment data. Failed restoration or cleanup
publishes `failed`; recovered rejection publishes `running` with a safe rejection category.
No new setting or environment variable is required. Existing startup and stop deadlines apply.

Process start, stop, and the complete reconfiguration decision are serialized by the registry
lifecycle lock. Peer child processes continue serving requests during the operation. Exit
notifications resolve the currently accepted worker ID; retired or abandoned candidate events
cannot mark a newer generation failed.

If a child resists cleanup, ownership remains reachable for a later `stop(instance_id)` or
`stop_all()` retry, including cleanup-only entries. `clear()` and `restore_snapshot()` refuse
to discard registry state while process cleanup remains pending. Resolve the cleanup failure
and retry the operation rather than replacing registry state around a live child.

### `McpProcessSupervisor`

- Always uses `multiprocessing.get_context("spawn")` (Qt-safe; portable).
- `spawn_worker` accepts optional typed proxy settings with local defaults
  (`server_type="local"`, `upstream_url=None`, `upstream_transport="streamable_http"`,
  `headers=None`, `timeout=30.0`) and copies `headers` into the `START` IPC message
  (PYPOST-1464).
- `update_tools(instance_id, tools) -> bool` checks that the worker record is `running`
  and `process.is_alive()`, encodes `tools` via `encode_tools`, sends `UPDATE_TOOLS` over
  `parent_conn`, logs `mcp_worker_update_tools_sent instance_id=%s tool_count=%d`, and
  returns `False` (logging `mcp_worker_update_tools_send_failed`) on broken pipes or
  serialization errors without raising (PYPOST-1465).
- Process table: `instance_id` → process handle, duplex Pipe, dedicated IPC reader
  thread, state (`starting` / `running` / `failed` / `stopped`).
- One demux reader per worker owns `poll`+`recv` (no shared Pipe drain races) and traces
  worker acknowledgments (`mcp_worker_ipc_ack`) and sanitized worker errors
  (`mcp_worker_ipc_error`).
- Monitor loop watches `process.is_alive()` / `exitcode`. When auto-restart is enabled and the
  worker was `running`, it schedules exponential backoff and respawns up to `max_retries`. If
  retries are exhausted, auto-restart is disabled, or exit occurred during initial startup
  (`starting`), it invokes `on_unexpected_exit` → registry marks the instance `failed`.
- Default stop budget: `DEFAULT_STOP_BUDGET_S = 2.0`.

### `mcp_worker_process.worker_main`

Headless spawn entrypoint. Must not import PySide6. On `START`, selects
`MCPProxyServerImpl` when `server_type == "proxy"` (supplying `upstream_url`,
`upstream_transport`, copied `headers`, `timeout`, and `_SnapshotStore`
variable/key suppliers) or `MCPServerImpl` otherwise (registering decoded local
tools only for local servers; PYPOST-1464). On `UPDATE_TOOLS`, decodes incoming
tools via `decode_tools`, calls `impl.register_tools(tools)` on `MCPServerImpl`
(atomically replacing `tools_map`), and responds with `ACK(correlating="UPDATE_TOOLS")`
or `WORKER_ERROR` (logging exception class name only via `mcp_worker_update_tools_failed`;
PYPOST-1465). Runs uvicorn on a private asyncio loop
via `_run_uvicorn(impl: MCPServerImpl | MCPProxyServerImpl, ...)`. Disables uvicorn
signal handlers so the **supervisor** owns SIGTERM/SIGKILL; the child reacts to IPC
`STOP` primarily.

---

## IPC contracts

Envelopes are dicts with `"v": 1` and `"type": <MsgType>` (`mcp_worker_ipc.make_message`).

| Direction | Type | Payload (conceptual) |
| --- | --- | --- |
| Host → Child | `START` | Server config, tools, variable snapshot, proxy settings |
| Host → Child | `UPDATE_TOOLS` | `tools` (encoded via `encode_tools`) |
| Host → Child | `UPDATE_VARIABLES` | `variables`, `hidden_keys`, `overridable_keys` |
| Host → Child | `HEARTBEAT` | optional `nonce` |
| Host → Child | `STOP` | — |
| Host → Child | `DEBUG_ABORT` / `DEBUG_HANG` | gated by `PYPOST_MCP_ALLOW_DEBUG_IPC` |
| Child → Host | `STARTED` | `pid`, `host`, `port` |
| Child → Host | `START_FAILED` | `message` |
| Child → Host | `HEARTBEAT_PONG` | `nonce` |
| Child → Host | `ACK` | e.g. `correlating="UPDATE_TOOLS"` or `"UPDATE_VARIABLES"` |
| Child → Host | `EXITED` | after cooperative STOP |
| Child → Host | `WORKER_ERROR` | fatal / sanitized command error path |
| Child → Host | `VERSION_MISMATCH` | unsupported protocol version error reply |

Tools are JSON-safe via `encode_tools` / `decode_tools` (`__mcp_tool_kind__`:
`http` | `websocket`).

### Tool & variable sync

| Mode | Mechanism |
| --- | --- |
| Thread | Live closures; updates tools in place; restarts on tool signature change |
| Process | Zero-downtime atomic tool and variable updates via IPC messages |

Never pickle host closures, runtime HTTP clients, or Qt objects into the child.
For proxy servers (`server_type="proxy"`), header templates are forwarded as primitive
configuration and resolved inside the owning child process against its own
`_SnapshotStore`; `START`, `UPDATE_TOOLS`, and `UPDATE_VARIABLES` payloads,
`upstream_url`, header values, request URLs/descriptions, and variable snapshots
are never logged.

### IPC protocol versioning and mismatch rejection (PYPOST-1467)

To prevent corrupted IPC states or silent failures caused by version skew between the host
supervisor and isolated child worker processes, all IPC message envelopes undergo strict version
validation upon ingress.

#### Envelope contracts

- **Current version**: `MSG_V = 1` (`pypost/core/mcp_worker_ipc.py`).
- **Supported versions**: `SUPPORTED_MSG_VERSIONS = frozenset({1})`.
- **Validation helper**: `validate_message_version(message: dict[str, Any]) -> int`.
  - Enforces that `message` is a dictionary containing a `"v"` key.
  - Enforces that `"v"` is a strict integer (rejects `bool`, `str`, `float`, `None`, and
    collections).
  - Enforces that `"v" in SUPPORTED_MSG_VERSIONS`.
  - Raises `McpProtocolVersionError` (subclass of `ValueError`) on failure, carrying
    `received_v` and `supported_versions` diagnostic attributes.

#### Worker ingress rejection semantics

In `mcp_worker_process.worker_main`:

- **Pre-START phase** (`store is None`): When the worker receives an envelope with an invalid or
  unsupported version before initialization, it logs `mcp_worker_ipc_version_rejected` at
  `WARNING` level, replies with `START_FAILED` containing the version error description, and
  exits immediately without starting uvicorn or leaking background threads.
- **Running phase** (`store is not None`): When a running worker receives an incompatible
  command (e.g. invalid `UPDATE_TOOLS` or `UPDATE_VARIABLES`), it logs
  `mcp_worker_ipc_version_rejected` at `WARNING` level, replies with `WORKER_ERROR`, discards
  the invalid payload, and continues serving without crashing uvicorn.

#### Supervisor ingress rejection semantics

In `mcp_process_supervisor.McpProcessSupervisor._apply_ipc_message`:

- **Starting phase** (`record.state == "starting"`): When the supervisor receives an envelope with
  an unsupported version from a launching worker, it logs `mcp_supervisor_ipc_version_rejected`
  at `ERROR` level, marks the worker record as `failed`, records `last_error`, and unblocks
  waiting callers by signaling `record.started_event`.
- **Running phase** (`record.state == "running"`): When the supervisor receives an incompatible
  envelope from an active worker, it logs `mcp_supervisor_ipc_version_rejected` at `ERROR` level,
  discards the message, and preserves supervisor state without corrupting the worker table.

#### Observability log events

IPC version rejection operations emit structured key-value events with strict secret safety:

| Event | Level | Key Fields | Description |
| --- | --- | --- | --- |
| `mcp_worker_ipc_version_rejected` | WARN | `received_v`, `supported` | Mismatch reject |
| `mcp_supervisor_ipc_version_rejected` | ERROR | `instance_id`, `received_v` | Mismatch reject |

Both events capture `received_v`, `supported_versions`, and the formatted error message, while
`mcp_supervisor_ipc_version_rejected` additionally records `instance_id`. All events strictly
omit payload bodies, tool parameters, environment variables, and authentication tokens.

---

## Stop escalation (SIGTERM → SIGKILL)

`McpProcessSupervisor.stop_worker(instance_id, timeout=None)` within the stop budget
(~2.0s by default):

1. Send IPC `STOP` (child sets `uvicorn.Server.should_exit`, joins serve thread, may
   send `EXITED`).
2. `process.join` for remaining budget.
3. If still alive: `process.terminate()` (SIGTERM / Windows terminate) and short join.
4. If still alive: `process.kill()` (SIGKILL / TerminateProcess) and final join.
5. Once the child is dead, stop IPC reader, close Pipe, and remove its process-table entry.
   If it remains alive, return failure and retain ownership so a later stop can retry.

Structured logs: `mcp_worker_stop_requested`, `mcp_worker_terminate` (`signal=SIGTERM`),
`mcp_worker_kill` (`signal=SIGKILL`), `mcp_worker_stop_finished`.

`DEBUG_HANG` (when allowed) ignores cooperative `STOP` so tests exercise the
SIGTERM→SIGKILL path. `DEBUG_ABORT` calls `os._exit(1)` to prove peer servers and the
host survive a fatal child exit.

---

## Auto-restart policy with exponential backoff (PYPOST-1466)

Process mode provides crash recovery for isolated worker processes that exit unexpectedly
from `running` state. When auto-restart is enabled, the supervisor automatically schedules
recovery attempts using capped exponential backoff, preserving peer server isolation and
avoiding manual operator intervention.

### Configuration via `McpWorkerRestartPolicy`

The policy is configured on `AppSettings.mcp_restart_policy` (and passed to `MCPServerRegistry`
and `McpProcessSupervisor`):

- `enabled: bool = False`: Opt-in toggle. Default `False` maintains immediate crash containment
  where unexpected child exits transition directly to `failed` without retrying (`FR1`).
- `max_retries: int = 3`: Maximum consecutive restart attempts (`0` to `100`).
- `initial_backoff_s: float = 0.5`: Delay in seconds before attempt 1 (`> 0.0`).
- `max_backoff_s: float = 8.0`: Maximum capped backoff delay (`> 0.0`, `>= initial_backoff_s`).
- `backoff_multiplier: float = 2.0`: Multiplier applied per retry attempt (`>= 1.0`).
- `healthy_reset_window_s: float = 30.0`: Required sustained uptime in seconds before the
  consecutive failure counter resets to 0 (`>= 0.0`).

### Exponential calculation formula

The delay for attempt $k \in \{1 \dots \text{max\_retries}\}$ is computed via
`policy.backoff_for_attempt(attempt)`:

$$\text{delay} = \min(
    \text{max\_backoff\_s},
    \text{initial\_backoff\_s} \times \text{backoff\_multiplier}^{(\text{attempt} - 1)}
)$$

Default progression:
- Attempt 1: $0.5 \times 2.0^0 = 0.5\,\text{s}$
- Attempt 2: $0.5 \times 2.0^1 = 1.0\,\text{s}$
- Attempt 3: $0.5 \times 2.0^2 = 2.0\,\text{s}$
- Capped at `max_backoff_s` ($8.0\,\text{s}$) for higher retry counts.

### Non-blocking deadline scheduling & monotonic timers

The supervisor's `_monitor_loop` detects child termination every 100 ms without blocking:

1. When a running worker crashes, the supervisor checks whether `policy.enabled` is `True`
   and `retry_count < policy.max_retries`.
2. If retries remain, the supervisor increments `retry_count`, transitions `record.state`
   to `starting` (recovering), records `next_retry_deadline = time.monotonic() + delay_s`, and
   notifies the registry via `on_worker_restarting(instance_id, attempt, delay_s, exitcode)`.
   The registry sets status to `starting` with an explanatory message:
   `Restarting after crash (attempt {attempt}/{max_retries} in {delay_s:.1f}s)`.
3. An asynchronous restart attempt thread (`_attempt_restart`) waits on the worker's
   `cancel_event` until the monotonic deadline expires.
4. When the deadline elapses without cancellation, the supervisor spawns a new worker child
   using `spawn_worker`. On receiving `STARTED`, `record.state` transitions back to `running`,
   `started_at` is stamped with `time.monotonic()`, and `on_worker_restarted` returns registry
   status to `running`.
5. If retries are exhausted (`retry_count >= max_retries`), the supervisor transitions `state`
   to `failed`, logs `mcp_worker_restart_exhausted`, and notifies `on_unexpected_exit`.

### Consecutive failure counter reset

To distinguish transient faults from permanent broken states, the supervisor monitors continuous
uptime:

- When a recovered worker remains continuously `running` for `healthy_reset_window_s`
  (default 30.0s), the monitor loop resets `retry_count = 0` and logs
  `mcp_worker_restart_counter_reset`.
- If the worker crashes hours or days later, it receives a full retry quota instead of
  failing prematurely (`FR4`).

### Immediate cancellation on operator stop, reconfigure, or shutdown

Restart delays never delay or block administrative operations (`FR6`):

- When an operator invokes `stop_worker(instance_id)`, `reconfigure(instance_id, ...)`, or
  supervisor `shutdown()`, the supervisor sets `cancel_event`.
- The restart thread aborts its backoff sleep in milliseconds, cleans up temporary process
  handles, and logs `mcp_worker_restart_cancelled` (`reason="operator_stop"` or
  `reason="supervisor_shutdown"`).
- In-flight restart timers do not block application exit or configuration changes.

### State snapshot preservation across restarts (`_WorkerSpawnSpec`)

During initial spawn, `McpProcessSupervisor` stores a typed `_WorkerSpawnSpec` on `_WorkerRecord`:

- Captures `host`, `port`, `name`, `tools`, `variables`, `hidden_keys`, `overridable_keys`,
  `server_type`, `upstream_url`, `upstream_transport`, `headers`, and `timeout`.
- When tools or variables are refreshed at runtime (`update_tools` / `update_variables` via
  collection updates or settings), the supervisor updates `_WorkerSpawnSpec` in place even while
  the worker child is down or waiting in backoff (`FR5`).
- The respawned child process is launched with the freshest tool catalog, variable values,
  and proxy headers rather than stale start-time arguments.

### Fast startup failure distinction (`FR7`)

Auto-restart is strictly a post-start crash recovery mechanism:

- If a worker fails during initial launch (e.g., port already bound, invalid socket address,
  missing dependencies, or spawn error), the child emits `START_FAILED` and exits with
  prior state `starting`.
- Fast startup failures bypass the restart retry loop entirely. The supervisor cleans up the
  failed child process, logs `mcp_worker_unexpected_exit prior_state=starting`, and transitions
  to terminal `failed` with the startup error.

### Observability log events and secret safety (`FR8`)

Supervisor and registry lifecycle transitions emit structured key-value events. Context
fields (`instance_id`, `pid`, `port`, `attempt`, `attempts`, `max_retries`, `delay_s`, `exitcode`,
`uptime_s`, `previous_retry_count`, `reason`) provide visibility without leaking secrets:

| Event Name | Level | Key Fields | Description |
| --- | --- | --- | --- |
| `mcp_worker_restart_scheduled` | INFO | `attempt`, `delay_s` | Scheduled backoff delay |
| `mcp_worker_restarted` | INFO | `pid`, `attempt` | Worker respawned and listening |
| `mcp_worker_restart_exhausted` | ERROR | `attempts`, `exitcode` | Retries exhausted; `failed` |
| `mcp_worker_restart_counter_reset` | INFO | `uptime_s` | Counter reset after healthy window |
| `mcp_worker_restart_cancelled` | INFO | `attempt`, `reason` | Cancelled on stop or shutdown |
| `mcp_registry_worker_restarting` | INFO | `attempt`, `delay_s` | Transitional `starting` |
| `mcp_registry_worker_restarted` | INFO | `attempt` | Registry transitioned to `running` |

All events strictly omit sensitive data: variable maps, resolved tokens, headers, upstream URLs,
and tool parameter schemas are never logged.

---

## Resource limits and spawn admission (PYPOST-1469)

Process mode provides host protection via configurable per-worker memory ceilings and
admission control on `McpProcessSupervisor`. This prevents runaway memory leaks or excess
spawns from starving peer services or triggering operating system OOM kills.

### Spawn admission gate (`McpAdmissionError`)

Before creating child processes or IPC pipes in `spawn_worker`, the supervisor validates
available capacity via `_check_admission(instance_id)`:

1. **Active worker count**: Counts all workers currently in `starting`, `running`, or
   `restarting` states. If `max_process_workers > 0` and active count exceeds the cap,
   spawn is rejected.
2. **Projected memory budget**: If `max_total_rss_mb > 0.0`, sums sampled resident memory
   (`rss_mb`) of all other active workers (using `default_worker_rss_estimate_mb` when not yet
   sampled) plus `default_worker_rss_estimate_mb` for the candidate. If the projected total
   exceeds `max_total_rss_mb`, spawn is rejected.
3. **Actionable failure**: Rejections raise `McpAdmissionError` (a `ValueError` subclass)
   and log `mcp_worker_spawn_admission_rejected` at `WARNING` level with instance and reason.
   Active running peers continue serving requests without disruption.

### Periodic Linux procfs memory sampling

The supervisor monitor loop (`_monitor_loop`) periodically samples child resident memory:

- **Linux procfs sampling**: Reads `VmRSS` from `/proc/{pid}/status` in megabytes. Incurs
  sub-millisecond overhead without forking helper processes or invoking C-extensions.
- **Fail-safe fallback**: Transient read errors or non-Linux platforms return safe `None`
  without interrupting the supervisor monitor loop.
- **Configurable interval**: `memory_sample_interval_s` (default 1.0s) throttles sampling
  frequency to minimize CPU overhead.
- **Test injection**: An injectable `rss_sampler` callable allows unit tests to simulate
  arbitrary memory usage profiles deterministically.

### Soft warnings and hard threshold escalation

The supervisor enforces dual memory thresholds on active workers:

- **Soft warning (`soft_memory_limit_mb`)**:
  - When worker RSS meets or exceeds `soft_memory_limit_mb`, the supervisor emits
    `mcp_worker_memory_warning` at `WARNING` level with `instance_id`, `pid`, `rss_mb`,
    and `soft_limit_mb`.
  - A stateful hysteresis flag (`soft_limit_warned`) ensures warnings fire exactly once per
    threshold crossing. The flag resets if RSS drops back below the soft limit.
  - The worker process continues running and serving requests normally.
- **Hard threshold escalation (`hard_memory_limit_mb`)**:
  - When worker RSS meets or exceeds `hard_memory_limit_mb`, the supervisor logs
    `mcp_worker_memory_exceeded` at `ERROR` level.
  - The supervisor escalates termination immediately: `process.terminate()` (SIGTERM),
    joins briefly, and issues `process.kill()` (SIGKILL) if still alive.
  - Sets worker state to `failed` with reason `memory_limit_exceeded`, cancels pending
    restarts (`cancel_event.set()`), and notifies the registry via unexpected exit.

### Auto-restart recovery harmonization

Auto-restart and admission control work cooperatively to prevent restart thrashing:

- When an auto-restart backoff delay expires in `_attempt_restart`, the supervisor checks
  admission (`_check_admission(instance_id, is_restart=True)`) before respawning.
- If the worker cap or aggregate memory budget is exhausted, `McpAdmissionError` is caught.
- The supervisor logs `mcp_worker_restart_admission_rejected` at `ERROR` level, cancels
  further retries (`restarting = False`, `next_retry_deadline = None`), marks the worker
  `failed` with the admission error message, and invokes `on_unexpected_exit`.
- This halts exponential backoff cycles gracefully rather than looping indefinitely under
  resource exhaustion.

### Observability log events

Supervisor resource limit operations emit structured key-value events:

| Event Name | Level | Key Fields | Description |
| --- | --- | --- | --- |
| `mcp_worker_spawn_admission_rejected` | WARN | `instance_id` | Spawn admission rejected |
| `mcp_worker_memory_warning` | WARN | `instance_id`, `pid` | Soft limit warning emitted |
| `mcp_worker_memory_exceeded` | ERROR | `instance_id`, `pid` | Hard ceiling SIGTERM/KILL |
| `mcp_worker_restart_admission_rejected` | ERROR | `instance_id` | Restart halted by limits |

Events strictly omit sensitive runtime data (no payload bodies, variables, or tokens).

## Active Heartbeat Watchdog (PYPOST-1468)

Isolated process-mode workers run an active heartbeat watchdog between the host supervisor and
child worker processes. This detects worker hangs, deadlocks, and event-loop freezes where the OS
process remains alive (`process.is_alive() == True`) but fails to respond to requests or commands.

### Nonce ping/pong protocol exchange (`HEARTBEAT`, `HEARTBEAT_PONG`)

Active probing uses a nonce-correlated protocol over the bidirectional worker IPC pipe:

1. **Probe Dispatch**:
   - The supervisor generates an ephemeral 16-character hexadecimal nonce (`uuid.uuid4().hex[:16]`).
   - Stored in the worker's record as `pending_heartbeat_nonce` with `pending_heartbeat_sent_at`.
   - Dispatched across the control pipe as `make_message("HEARTBEAT", nonce=nonce)`.
2. **Worker Echo**:
   - In `mcp_worker_process.worker_main`, the worker IPC polling loop receives `HEARTBEAT`.
   - It immediately replies with `make_message("HEARTBEAT_PONG", nonce=message.get("nonce"))`.
3. **Supervisor Nonce Verification**:
   - In `McpProcessSupervisor._apply_ipc_message`, incoming `HEARTBEAT_PONG` messages are validated.
   - If `received_nonce == record.pending_heartbeat_nonce`, the probe roundtrip is confirmed.
   - Supervisor calculates `latency_s = now - record.pending_heartbeat_sent_at`, logs
     `mcp_worker_heartbeat_pong` at `DEBUG` level, stamps `record.last_heartbeat_pong_at = now`,
     and clears `pending_heartbeat_nonce`.
   - If the received nonce does not match (or probe was already cleared/timed out), the supervisor
     logs `mcp_worker_heartbeat_pong_mismatch` at `WARNING` level and discards the message without
     clearing the in-flight probe.

### Supervisor active probe evaluation in `_monitor_loop`

The supervisor's dedicated background thread (`_monitor_loop`) polls every 50 ms to evaluate
worker health:

- **Eligibility**: Probing runs when `heartbeat_policy.enabled` is `True`, worker state is
  `running`, `not record.restarting`, and `record.process.is_alive()`.
- **Interval Check**: If no probe is currently pending (`pending_heartbeat_nonce is None`) and
  `now - record.last_heartbeat_sent_at >= heartbeat_policy.interval_s`, the supervisor generates
  a fresh nonce, stamps `last_heartbeat_sent_at`, and sends `HEARTBEAT`.
- **Timeout Check**: If a probe is pending (`pending_heartbeat_nonce is not None`), the supervisor
  compares elapsed time `now - record.pending_heartbeat_sent_at` against `timeout_s`. If elapsed
  time exceeds `timeout_s`, the watchdog escalates to process termination.

### Watchdog timeout escalation (SIGTERM → SIGKILL)

When a pending probe times out:

1. **Timeout Logging**: Supervisor logs `mcp_worker_heartbeat_timeout` at `ERROR` level with
   `instance_id`, child `pid`, and configured `timeout_s`.
2. **Process Escalation**:
   - The supervisor sends `process.terminate()` (SIGTERM / TerminateProcess).
   - Waits up to 0.2s for graceful exit via `process.join(timeout=0.2)`.
   - If the process is still alive, escalates to `process.kill()` (SIGKILL).
3. **Record Cleanup**:
   - Clears `pending_heartbeat_nonce` and `pending_heartbeat_sent_at`.
   - Sets `record.last_error = f"heartbeat timeout ({timeout_s}s)"`.
   - Schedules reader thread termination via `readers_to_stop`.

### Auto-restart interplay

Watchdog timeout integrates seamlessly with `McpWorkerRestartPolicy`:

- **Auto-restart Enabled (`restart_policy.enabled=True`)**:
  - If `record.retry_count < restart_policy.max_retries`:
    - Supervisor increments `retry_count`, computes backoff delay via `backoff_for_attempt`,
      stamps `next_retry_deadline = now + delay_s`, sets `record.restarting = True`, and updates
      `record.state = "starting"`.
    - Logs `mcp_worker_restart_scheduled` with `reason=heartbeat_timeout`.
    - Dispatches `on_worker_restarting` notification to the registry.
    - When backoff deadline expires, supervisor spawns a new worker child with preserved spec.
  - If retries are exhausted (`retry_count >= restart_policy.max_retries`):
    - Supervisor marks `record.state = "failed"`, logs `mcp_worker_restart_exhausted`, and
      dispatches `on_unexpected_exit(instance_id, exitcode)`.
- **Auto-restart Disabled (`restart_policy.enabled=False`)**:
  - Supervisor transitions `record.state = "failed"` immediately upon timeout termination.
  - Sets `record.cancel_event.set()` and dispatches `on_unexpected_exit`.
  - Registry marks the instance `failed` with descriptive `last_error`.

### Observability events

Watchdog operations emit structured key-value events with strict secret safety:

| Event Name | Level | Key Fields | Description |
| --- | --- | --- | --- |
| `mcp_worker_heartbeat_timeout` | ERROR | `instance_id`, `pid`, `timeout_s` | Watchdog timeout |
| `mcp_worker_heartbeat_pong` | DEBUG | `instance_id`, `pid`, `latency_s` | Valid pong roundtrip |
| `mcp_worker_heartbeat_pong_mismatch` | WARN | `expected`, `got` | Stale or invalid nonce |
| `mcp_worker_restart_scheduled` | INFO | `instance_id`, `attempt`, `delay_s` | Respawn scheduled |

All events omit secret credentials, tokens, payloads, and environment variables. Nonces are
ephemeral random hex strings.

---

## High-density 10x process-mode stress parity (PYPOST-1470)

Standalone MCP servers in process execution mode (`mcp_execution_mode = "process"`) have
full operational parity with thread-mode servers under high-concurrency workloads. The
stress suite (`tests/test_mcp_process_stress_10x.py`) exercises multi-process density,
isolation guarantees, fault recovery, and socket lifecycle management across 10 concurrent
worker processes.

### 10x barrier synchronization startup

To stress process table allocation, pipe creation, and simultaneous uvicorn initialization:

- **Barrier-synchronized launch**: A `threading.Barrier(10)` synchronizes 10 executor threads,
  triggering concurrent `registry.start()` calls for 10 isolated process servers at the exact
  same instant.
- **Port readiness**: Verifies that all 10 worker processes transition to `running`, bind their
  respective ephemeral ports, and report active listening status within bounded deadlines.
- **Concurrent tool discovery**: Immediately dispatches concurrent `_mcp_list_tools` requests
  across all 10 running processes, ensuring zero deadlocks, race conditions, or supervisor
  lock contention during startup.

### Concurrent request variable namespace isolation

To ensure complete tenant separation and verify that child processes never share memory:

- **Distinct namespace bindings**: 10 standalone process workers are initialized with identical
  variable key names bound to unique, server-specific values.
- **High-throughput load**: A `ThreadPoolExecutor` dispatches 100 parallel tool requests (10
  concurrent requests per worker across all 10 servers).
- **Echo gate verification**: Under `PYPOST_MCP_TEST_ECHO_VARS=1`, workers echo runtime variable
  snapshots back to the caller.
- **Zero cross-talk**: Asserts 100% data isolation across all 100 responses, verifying that
  concurrent request processing across OS processes never leaks state or environment variables.

### Abrupt client disconnect and TCP RST resilience

To validate supervisor and worker fault tolerance against broken network connections:

- **TCP RST injection**: Establishes raw TCP client sockets to all 10 running servers, transmits
  partial HTTP request payloads, and forcefully resets the connection using `SO_LINGER` with a
  timeout of 0 seconds (`struct.pack("ii", 1, 0)`).
- **Graceful connection handling**: Confirms that worker asyncio event loops handle connection
  resets cleanly without crashing or corrupting server state.
- **Subsequent request continuity**: Validates that all 10 workers remain alive and immediately
  serve subsequent valid tool calls (`_mcp_call_tool`) without requiring restarts.

### Concurrent teardown and ephemeral port reclamation

To guarantee clean operating system resource hygiene on server termination:

- **Parallel shutdown**: Coordinates concurrent termination of all 10 servers via
  `registry.stop_all()`.
- **Bounded termination budget**: All 10 worker processes exit cleanly within the supervisor's
  stop budget (`DEFAULT_STOP_BUDGET_S = 2.0`).
- **Zero port collisions**: Uses `EphemeralPortReserve.verify_all_rebound()` to rebind standard
  TCP listening sockets to all 10 allocated ports immediately after teardown, confirming zero
  `EADDRINUSE` errors, zero zombie handles, and total socket reclamation.

### Windows stop escalation simulation

To verify stop escalation when a process worker becomes uncooperative:

- **Simulated hang**: Uses `DEBUG_HANG` opcode under `PYPOST_MCP_ALLOW_DEBUG_IPC=1` to simulate a
  worker process that ignores cooperative `STOP` IPC messages.
- **Progressive escalation**: Asserts that the supervisor escalates from cooperative `STOP` to
  `process.terminate()` and `process.kill()` within the allocated stop budget.
- **Strict budget ceiling**: Validates that shutdown completes within `DEFAULT_STOP_BUDGET_S` plus
  grace window, without blocking the host application or leaving orphaned processes.

---

## Cross-platform Windows stop escalation and CI workflow (PYPOST-1470)

Operating systems manage process lifecycles and forceful termination differently. Process mode
provides uniform termination semantics across POSIX and Windows platforms.

### Win32 `TerminateProcess` vs POSIX signals

| Dimension | POSIX (Linux / macOS) | Windows (Win32) |
| --- | --- | --- |
| Graceful signal | `SIGTERM` (15) | Not supported (uses IPC `STOP`) |
| Forceful kill | `SIGKILL` (9) | `TerminateProcess(handle, 1)` |
| Python API | `process.terminate()`, `kill()` | `process.terminate()`, `kill()` |
| Exit code | Negative signal (`-15`, `-9`) | Exit code `1` |
| Signal trapping | `SIGTERM` catchable; `SIGKILL` non-maskable | Neither catchable |
| Cleanup hooks | `finally` / `atexit` may run on `SIGTERM` | Immediately unmapped; no hooks run |
| Handle reclamation | Closes file descriptors on exit | Closes object handles on exit |

In `McpProcessSupervisor.stop_worker`:

1. **Cooperative phase**: Dispatches IPC `STOP` message. The worker receives the message, initiates
   graceful uvicorn shutdown, and exits cooperatively.
2. **First escalation**: If the worker remains alive after the stop budget, calls
   `process.terminate()`. On POSIX, this sends `SIGTERM`. On Windows, this invokes
   `TerminateProcess(handle, 1)`.
3. **Final escalation**: If still alive after a short bounded wait, calls `process.kill()`. On
   POSIX, this sends `SIGKILL`. On Windows, this repeats `TerminateProcess(handle, 1)`.
4. **Platform-agnostic verification**: Tests assert that the process table is cleared and child
   processes terminate cleanly, accounting for platform-specific exit codes (`1` on Windows,
   `-SIGTERM` / `-SIGKILL` on POSIX).

### Dedicated `windows-process-stop` GitHub Actions CI workflow

Process lifecycle behavior and handle cleanup on Windows are verified in continuous integration:

- **Workflow job**: `.github/workflows/test.yml` defines the `windows-process-stop` job.
- **Runner environment**: Runs on `windows-latest` with Python 3.11 and `timeout-minutes: 15`.
- **Headless configuration**: Sets `QT_QPA_PLATFORM: offscreen` to allow PySide6 / Qt initialization
  in headless Windows CI runners.
- **Test execution**: Runs the stress parity and process isolation repro suites:
  ```powershell
  python -m pytest tests/test_mcp_process_stress_10x.py `
    tests/test_mcp_process_isolation_repro.py -v --tb=short
  ```
- **Step summary**: Emits markdown report to `$GITHUB_STEP_SUMMARY` logging test suite execution.

### Running tests locally and in CI

#### Local execution (Linux / macOS)

Run the 10x process-mode stress parity suite via the standard Makefile target:

```bash
make test WORKERS=1 PYTEST_ARGS="tests/test_mcp_process_stress_10x.py -v"
```

To run both process isolation repro and 10x stress suites together:

```bash
make test WORKERS=1 \
  PYTEST_ARGS="tests/test_mcp_process_stress_10x.py \
  tests/test_mcp_process_isolation_repro.py -v"
```

#### Local execution (Windows)

On Windows developer machines without `make`, run pytest directly from the virtual environment:

```powershell
python -m pytest tests/test_mcp_process_stress_10x.py -v --tb=short
```

#### Continuous integration (CI)

Every pull request and commit to `dev` automatically triggers:
- Linux test matrix (`ubuntu-latest` with Python 3.11 and 3.13) via `make check`.
- Windows process stop escalation suite (`windows-latest`) via `windows-process-stop`.

---

## Troubleshooting

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| Start fails / never `STARTED` | Bind, import, or timeout | Check `last_start_error`; free port |
| Peer dies on crash | Registry on `thread` | Set `mcp_execution_mode="process"` |
| Edits missing / row `failed` | Worker exited or bad ref | Check logs; restart failed server |
| Empty / wrong vars in test | Echo gate unset | Export `PYPOST_MCP_TEST_ECHO_VARS=1` |
| Debug opcode raises/ignored | Debug gate unset | Set `PYPOST_MCP_ALLOW_DEBUG_IPC=1` |
| Stop hangs past ~2s | Budget should force kill | Check `mcp_worker_kill` logs |
| Mode change ignored | Mode is construction-time | Stop servers and recreate registry |
| Crash loop exhausted | Crashes exceeded retries | Check logs, fix fault, restart |
| Startup failure not retried | Fast startup failure | Verify port free and valid address |
| Pending restart delay | Exponential backoff active | Wait for delay or call stop to abort |
| Spawn rejected (`McpAdmissionError`) | Cap/budget reached | Stop idle servers or raise limits |
| Memory warning in logs | Worker RSS exceeded soft limit | Inspect memory; recycle or tune limit |
| Killed: `memory_limit_exceeded` | RSS exceeded hard limit | Killed via SIGKILL; check leak |
| Restart halted by admission | Limits exceeded in backoff | Resolve pressure; restart when free |
| Worker start version mismatch | Incompatible protocol version | Ensure worker and host use `v=1` |
| Runtime command version rejected | Unsupported message `v` | Discarded as WORKER_ERROR (v=1) |
| Heartbeat timeout in logs | Worker frozen or deadlocked | Terminated to failed; tune timeout |
| 10x timeout under load | Port collision or thrashing | Ensure ports free; check host capacity |
| TCP RST causes crash | Broken pipe unhandled in loop | Verify transport error handling |
| Windows stop hangs | Handle leak or deadlock | Verify stop budget forces TerminateProcess |

For a rejected live edit, inspect `mcp_registry_process_reconfigure_rejected`: the `phase`,
`restored`, and `cleaned` fields distinguish startup, reclamation, and restoration outcomes
without exposing runtime secrets. `mcp_registry_process_reconfigured` records success.
If the resulting status is failed, correct endpoint/resource availability and retry cleanup
before restarting. `MCP worker cleanup remains pending` from clear/restore means retained
worker ownership must first be reclaimed through stop/stop_all.

---

## Automated tests

```bash
make test PYTEST_ARGS="tests/test_mcp_process_isolation_repro.py -v"
make test WORKERS=1 PYTEST_ARGS="tests/test_mcp_process_reconfigure_repro.py -q"
make test WORKERS=1 PYTEST_ARGS="tests/test_mcp_process_proxy_repro.py -q"
make test WORKERS=1 PYTEST_ARGS="tests/test_mcp_process_tool_refresh_repro.py -q"
make test WORKERS=1 PYTEST_ARGS="tests/test_mcp_process_autorestart_repro.py -q"
make test WORKERS=1 PYTEST_ARGS="tests/test_mcp_process_resource_limits_repro.py -q"
make test WORKERS=1 PYTEST_ARGS="tests/test_mcp_ipc_protocol_version_repro.py -q"
make test WORKERS=1 PYTEST_ARGS="tests/test_mcp_ipc_heartbeat_watchdog_repro.py -q"
make test WORKERS=1 PYTEST_ARGS="tests/test_mcp_process_stress_10x.py -v"
make test PYTEST_ARGS="tests/test_mcp_multiserver_stress_10x.py"
```

Process-mode coverage: setting default/validation, crash isolation, variable isolation
under load, bounded stop with unresponsive worker, thread-mode 10x regression control.
Reconfiguration coverage includes same/changed endpoints, bounded recovery and failed recovery,
peer continuity, candidate cleanup, concurrent stop/edit ordering, and cleanup retries.
Proxy parity coverage (`tests/test_mcp_process_proxy_repro.py`, PYPOST-1464) verifies
Streamable HTTP and SSE upstream forwarding in isolated worker processes, `START` IPC
proxy field propagation (`server_type`, `upstream_url`, `upstream_transport`, `headers`,
`timeout`), child-side header template resolution, live proxy reconfiguration, and
secret-safe structured logging.
Tool refresh parity coverage (`tests/test_mcp_process_tool_refresh_repro.py`, PYPOST-1465)
verifies live add/modify/remove tool refresh over `UPDATE_TOOLS` without PID/port change,
collection-scoped variable and secret refresh with active environment override preservation,
neighbor and proxy server isolation, dead-worker failure containment and `start_snapshot`
synchronization, thread-mode regression parity, and secret-safe structured logging.
Auto-restart recovery coverage (`tests/test_mcp_process_autorestart_repro.py`, PYPOST-1466)
verifies the 7 acceptance criteria:
1. `AppSettings.mcp_restart_policy` defaults, field bounds, and backoff formula calculations.
2. Default policy disabled (`enabled=False`): unexpected exits fail immediately without retries.
3. Exponential backoff recovery with state preservation across live tool and variable updates.
4. Retry exhaustion after `max_retries` consecutive failures transitioning to terminal `failed`.
5. Healthy uptime reset window resetting the retry counter after sustained normal operation.
6. Immediate backoff cancellation upon operator `stop_worker` and supervisor `shutdown`.
7. Fast startup failure bypass: initial bind errors fail immediately without triggering restart.
8. Observability structured logging and secret safety assertions verified via `caplog`.
Resource limits and admission coverage (`tests/test_mcp_process_resource_limits_repro.py`,
PYPOST-1469) verifies the 7 acceptance criteria:
1. `AppSettings.mcp_resource_limits` defaults, field bounds, and cross-field validation.
2. Default unlimited policy allows worker spawns without admission rejection.
3. Active worker count cap (`max_process_workers`) rejects excess spawns with `McpAdmissionError`.
4. Aggregate memory budget (`max_total_rss_mb`) rejects excess spawns based on projected RSS.
5. Soft memory limit emits `mcp_worker_memory_warning` once without killing the worker.
6. Hard memory limit triggers `SIGTERM` -> `SIGKILL` escalation, setting `memory_limit_exceeded`.
7. Admission exhaustion during auto-restart backoff halts recovery cycles gracefully.
IPC protocol versioning coverage (`tests/test_mcp_ipc_protocol_version_repro.py`, PYPOST-1467)
verifies strict envelope integer versioning, worker start rejection (`START_FAILED`), runtime
command rejection (`WORKER_ERROR`), supervisor ingress rejection during starting and running
states, and secret-safe structured logging via `caplog`.
Heartbeat watchdog coverage (`tests/test_mcp_ipc_heartbeat_watchdog_repro.py`, PYPOST-1468)
verifies the 6 acceptance criteria:
1. `AppSettings.mcp_heartbeat_policy` defaults, field bounds, and cross-field validation.
2. Normal worker heartbeats roundtrip successfully across multiple probe intervals.
3. Hung or deadlocked workers time out, undergo SIGTERM->SIGKILL escalation, and enter `failed`.
4. Disabled watchdog (`enabled=False`) preserves process without termination during freezes.
5. Watchdog timeout initiates automatic respawn cycles when auto-restart is enabled.
6. Mismatched or stale heartbeat pong nonces emit warning logs and are safely ignored.
10x process-mode stress parity and Windows stop escalation coverage
(`tests/test_mcp_process_stress_10x.py`, PYPOST-1470) verifies the 5 acceptance criteria:
1. 10x process barrier startup: barrier synchronization across 10 concurrent process workers with
   active listening status and simultaneous tool discovery.
2. 10x concurrent namespace isolation: 100 parallel requests across 10 workers with distinct values
   for identical variable keys with zero state leakage.
3. 10x abrupt client disconnect resilience: TCP RST mid-payload (`SO_LINGER=0`) fault tolerance
   preserving worker health and subsequent tool calls.
4. 10x concurrent teardown and port reclamation: parallel shutdown with immediate socket rebinding
   (`verify_all_rebound`) and zero `EADDRINUSE` collisions.
5. Cross-platform Windows stop escalation verification: graceful stop escalating to forceful
   `TerminateProcess` verified in test simulation and GitHub Actions `windows-latest` CI.

---

## Related documentation

- [Multi-Process Supervisor Evaluation (PYPOST-1438)](mcp_process_supervisor_evaluation.md)
- [MCP Reverse Proxy (PYPOST-1092)](mcp_proxy.md)
- [Concurrent Multi-Server Lifecycle (PYPOST-1418)](mcp_concurrent_multiserver.md)
- [Multiple Independent MCP Servers (PYPOST-1044)](mcp_server_registry.md)
- [Cancellation / adaptive join (PYPOST-1437)](mcp_concurrent_multiserver.md#cancellation)
