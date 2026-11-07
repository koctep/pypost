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
| Setting | `pypost/models/settings.py` | `mcp_execution_mode` |
| Registry | `pypost/core/mcp_server_registry.py` | Selects runner; maps unexpected child exit → `failed` |
| Protocol / runners | `pypost/core/mcp_server_runner.py` | `MCPServerRunnerProtocol`, `ThreadServerRunner`, `ProcessServerRunner` |
| Supervisor | `pypost/core/mcp_process_supervisor.py` | Process table, IPC send, STOP→SIGTERM→SIGKILL |
| IPC helpers | `pypost/core/mcp_worker_ipc.py` | Versioned envelopes (`v: 1`), tool encode/decode |
| Worker | `pypost/core/mcp_worker_process.py` | Spawn target; uvicorn + `MCPServerImpl` (local) or `MCPProxyServerImpl` (proxy) |

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
| `thread` (default) | In-process daemon threads; live variable supplier closures; cooperative cancel + `adaptive_thread_join` |
| `process` | One OS process per server via `multiprocessing.get_context("spawn")`; variable **snapshots** over IPC |

```python
from pypost.models.settings import AppSettings
from pypost.core.mcp_server_registry import MCPServerRegistry

settings = AppSettings(mcp_execution_mode="process")
registry = MCPServerRegistry(execution_mode=settings.mcp_execution_mode)
```

There is not yet a Settings dialog control for this field (tech debt); operators and
tests set it on `AppSettings` / registry construction.

### Environment gates (test / debug only)

| Variable | Effect |
| --- | --- |
| `PYPOST_MCP_ALLOW_DEBUG_IPC=1` | Allows supervisor `send_debug_opcode` and worker handling of `DEBUG_ABORT` / `DEBUG_HANG`. Without it, the supervisor raises; the worker logs and ignores. |
| `PYPOST_MCP_TEST_ECHO_VARS=1` | `MCPServerImpl` echoes `server_index` / `unique_secret` / `server_id` in the tool response body so process-mode isolation tests can assert snapshots without parent-side request mocks (which do not cross `spawn`). |

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
- `update_variables(variables, hidden_keys, overridable_keys) -> None`

`ServerStartSpec` carries configuration, tools, and the initial variable snapshot
(dict + key sets). Public registry start/stop/status semantics are unchanged
(`stopped` / `starting` / `running` / `failed`).

### `ThreadServerRunner`

Wraps `MCPServerManager`. Variable suppliers remain live `Callable` closures.
Stop uses `CancellationTokenSource` and `adaptive_thread_join` (default ~2.0s).

### `ProcessServerRunner`

Delegates to a shared `McpProcessSupervisor`. Forwards both local tool inputs and
proxy settings (`server_type`, `upstream_url`, `upstream_transport`, copied `headers`,
and `timeout`) from `ServerStartSpec.configuration` to `spawn_worker` (PYPOST-1464).
Converts supplier updates into `UPDATE_VARIABLES` IPC snapshots. Exposes
`send_debug_opcode` for tests only. The read-only `worker_id` identifies the supervisor
entry independently of the public configuration ID. `start_snapshot` returns a deep copy
of the accepted start payload (including proxy configuration); variable updates refresh
the snapshot used for recovery.

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
- Process table: `instance_id` → process handle, duplex Pipe, dedicated IPC reader
  thread, state (`starting` / `running` / `failed` / `stopped`).
- One demux reader per worker owns `poll`+`recv` (no shared Pipe drain races).
- Monitor loop watches `process.is_alive()` / `exitcode` only; unexpected exit
  invokes `on_unexpected_exit` → registry marks the instance `failed`.
- Default stop budget: `DEFAULT_STOP_BUDGET_S = 2.0`.

### `mcp_worker_process.worker_main`

Headless spawn entrypoint. Must not import PySide6. On `START`, selects
`MCPProxyServerImpl` when `server_type == "proxy"` (supplying `upstream_url`,
`upstream_transport`, copied `headers`, `timeout`, and `_SnapshotStore`
variable/key suppliers) or `MCPServerImpl` otherwise (registering decoded local
tools only for local servers; PYPOST-1464). Runs uvicorn on a private asyncio loop
via `_run_uvicorn(impl: MCPServerImpl | MCPProxyServerImpl, ...)`. Disables uvicorn
signal handlers so the **supervisor** owns SIGTERM/SIGKILL; the child reacts to IPC
`STOP` primarily.

---

## IPC contracts

Envelopes are dicts with `"v": 1` and `"type": <MsgType>` (`mcp_worker_ipc.make_message`).

| Direction | Type | Payload (conceptual) |
| --- | --- | --- |
| Host → Child | `START` | `host`, `port`, `name`, `tools` (encoded), `variables`, `hidden_keys`, `overridable_keys`, `server_type`, `upstream_url`, `upstream_transport`, `headers`, `timeout` |
| Host → Child | `UPDATE_VARIABLES` | `variables`, `hidden_keys`, `overridable_keys` |
| Host → Child | `HEARTBEAT` | optional `nonce` |
| Host → Child | `STOP` | — |
| Host → Child | `DEBUG_ABORT` / `DEBUG_HANG` | gated by `PYPOST_MCP_ALLOW_DEBUG_IPC` |
| Child → Host | `STARTED` | `pid`, `host`, `port` |
| Child → Host | `START_FAILED` | `message` |
| Child → Host | `HEARTBEAT_PONG` | `nonce` |
| Child → Host | `ACK` | e.g. `correlating="UPDATE_VARIABLES"` |
| Child → Host | `EXITED` | after cooperative STOP |
| Child → Host | `WORKER_ERROR` | fatal path |

Tools are JSON-safe via `encode_tools` / `decode_tools` (`__mcp_tool_kind__`:
`http` | `websocket`).

### Variable sync

| Mode | Mechanism |
| --- | --- |
| Thread | Live closures into the in-process ASGI impl |
| Process | Host sends snapshots; child `_SnapshotStore` feeds local callables |

Never pickle host closures, runtime HTTP clients, or Qt objects into the child.
For proxy servers (`server_type="proxy"`), header templates are forwarded as primitive
configuration and resolved inside the owning child process against its own
`_SnapshotStore`; `START` payloads, `upstream_url`, header values, and variable
snapshots are never logged.

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

## Troubleshooting

| Symptom | Likely cause | Resolution |
| --- | --- | --- |
| Process start fails / worker never `STARTED` | Bind error, spawn import error, or start timeout (15s) | Check `START_FAILED` / `last_start_error`; ensure port free; confirm worker import graph has no PySide6 |
| Peer servers die with one crash | Registry still on `thread` | Set `mcp_execution_mode="process"` and rebuild registry |
| Isolation test gets empty / wrong vars | Echo gate unset across spawn | Export `PYPOST_MCP_TEST_ECHO_VARS=1` **before** spawning workers |
| `send_debug_opcode` raises / DEBUG ignored | Debug gate unset | Set `PYPOST_MCP_ALLOW_DEBUG_IPC=1` in supervisor **and** child environment |
| Stop hangs past ~2s | Unexpected; budget should force kill | Check `mcp_worker_kill` logs; verify child not outside supervisor table |
| Mode change ignored while running | Mode is construction-time | Stop servers; recreate registry with the new `execution_mode` |

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

---

## Related documentation

- [Multi-Process Supervisor Evaluation (PYPOST-1438 / Phase 2)](mcp_process_supervisor_evaluation.md)
- [MCP Reverse Proxy (PYPOST-1092)](mcp_proxy.md)
- [Concurrent Multi-Server Lifecycle (PYPOST-1418)](mcp_concurrent_multiserver.md)
- [Multiple Independent MCP Servers (PYPOST-1044)](mcp_server_registry.md)
- [Cancellation / adaptive join (PYPOST-1437)](mcp_concurrent_multiserver.md#cooperative-cancellation-architecture-pypostcorecancellationpy)
