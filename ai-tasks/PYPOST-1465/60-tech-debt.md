# PYPOST-1465: Technical Debt Analysis

## Shortcuts Taken

No temporary stubs, bypasses, or hardcoded workarounds remain in the process-mode collection
refresh path:

- **In-place `UPDATE_TOOLS` IPC**: `McpProcessSupervisor.update_tools` sends `UPDATE_TOOLS` over the
  existing control pipe so the worker replaces `MCPServerImpl.tools_map` atomically without
  restarting the child process or rebinding the listening port. As with `START` and
  `UPDATE_VARIABLES`, `MSG_V = 1` is stamped on the envelope while active version negotiation on
  receive remains deferred to the dedicated sprint task
  ([PYPOST-1467](https://pypost.atlassian.net/browse/PYPOST-1467)).
- **Asynchronous IPC acknowledgment**: `McpProcessSupervisor.update_tools` validates that the worker
  is in `"running"` state and `process.is_alive()` is true, then writes `UPDATE_TOOLS` to the parent
  pipe without blocking the caller on a synchronous round-trip wait for `ACK`, matching the existing
  `UPDATE_VARIABLES` control-channel semantics. The dedicated supervisor reader thread logs
  `mcp_worker_ipc_ack` (`correlating=UPDATE_TOOLS`) or `mcp_worker_ipc_error` asynchronously.
- **Detect-and-fail on dead workers**: When a bound worker has exited or pipe delivery fails during
  `refresh_collection`, the registry marks that instance `failed` without automatic restart.
  Configurable auto-restart with backoff and active `HEARTBEAT` liveness probing remain tracked under
  [PYPOST-1466](https://pypost.atlassian.net/browse/PYPOST-1466) and
  [PYPOST-1468](https://pypost.atlassian.net/browse/PYPOST-1468).

## Code Quality Issues

No code-quality blocker was identified across the modified modules (`pypost/core/mcp_worker_ipc.py`,
`pypost/core/mcp_server_impl.py`, `pypost/core/mcp_worker_process.py`,
`pypost/core/mcp_process_supervisor.py`, `pypost/core/mcp_server_runner.py`,
`pypost/core/qt/mcp_server.py`, `pypost/core/mcp_server_registry.py`, and
`tests/test_mcp_process_tool_refresh_repro.py`):

- **Atomic tool map replacement**: `MCPServerImpl.register_tools` builds a new dictionary of
  deep-copied tool models and assigns `self.tools_map = new_map` in a single reference swap,
  preventing concurrent coroutines on the worker event loop from observing a partially populated tool
  catalog.
- **Runner protocol and snapshot parity**: `MCPServerRunnerProtocol`, `ThreadServerRunner`, and
  `ProcessServerRunner` all expose `update_tools(tools) -> bool`. `ProcessServerRunner.update_tools`
  and `update_variables` keep `self._spec` (`start_snapshot`) synchronized so subsequent
  `reconfigure` rollbacks restore the latest refreshed tools and variables rather than stale
  initial-start state.
- **Unified workspace and library collection refresh**: `MCPServerRegistry.refresh_collection`
  resolves tools and collection-scoped variables for both workspace-backed and library-backed local
  servers while ignoring proxy servers, and `MCPServerManager.update_tools` now refreshes in-place
  request edits even when the `(id, name)` signature is unchanged.
- **Static analysis and typing**: Production and Markdown lint (`make -o lint-tests lint`) and
  `make typecheck` pass with zero new warnings or errors. Test lint has only the pre-existing E501
  violation in `tests/test_mcp_server_registry.py:308:101` tracked under
  [PYPOST-1509](https://pypost.atlassian.net/browse/PYPOST-1509).

## Missing Tests

No missing test coverage is classified as a **BLOCKER**:

- **Timeout markers**: `tests/test_mcp_process_tool_refresh_repro.py` declares both a module-level
  `pytestmark = pytest.mark.timeout(60)` and per-test `@pytest.mark.timeout(60)` decorators across
  all five tests, satisfying repository pytest timeout rules.
- **Covered scenarios**: The acceptance suite verifies live tool addition, modification, and removal
  in process mode without worker restart or PID/port change; workspace and library-backed collection
  variable and secret updates with active environment preservation; neighbor collection and proxy
  server isolation; exited-worker failure containment and `start_snapshot` synchronization;
  shared-mode (`execution_mode="thread"`) regression parity; and `caplog` verification that
  structured logs never leak request URLs, descriptions, or secret variable values.
- **Broader stress and platform CI**: Process-mode 10x multi-server stress parity and Windows
  stop-escalation CI coverage remain tracked under
  [PYPOST-1470](https://pypost.atlassian.net/browse/PYPOST-1470).

## Performance Concerns

No new performance blocker was introduced by this task:

- **Sub-5 ms in-place IPC refresh**: Sending `UPDATE_TOOLS` and `UPDATE_VARIABLES` over the existing
  duplex pipe avoids ~150–350 ms `spawn` process restart latency and eliminates socket rebind races.
- **Full-snapshot serialization**: Each `refresh_collection` serializes the collection's tool models
  and merged variable dictionary in full rather than computing incremental diffs. This is negligible
  for typical collection sizes (tens of requests) and occurs only on operator collection edits.
- **Process memory ceilings**: Per-worker memory ceilings and spawn admission control for dense
  process-mode configurations remain tracked under
  [PYPOST-1469](https://pypost.atlassian.net/browse/PYPOST-1469).

## Follow-up Tasks

All follow-up items below are **NON-BLOCKER** and already tracked in Jira; no duplicate issues are
created by this task:

- **TD-1 — NON-BLOCKER — pre-existing**: Test lint reports
  `tests/test_mcp_server_registry.py:308:101: E501 line too long (111 > 100 characters)` when
  running `make lint` (reproduced at base commit `33d5cb1a`).
  Jira: [PYPOST-1509](https://pypost.atlassian.net/browse/PYPOST-1509).
- **TD-2 — NON-BLOCKER**: Configurable auto-restart policy with exponential backoff for unexpected
  MCP worker exits.
  Jira: [PYPOST-1466](https://pypost.atlassian.net/browse/PYPOST-1466).
- **TD-3 — NON-BLOCKER**: IPC protocol version (`MSG_V`) negotiation and mismatch rejection between
  supervisor and worker.
  Jira: [PYPOST-1467](https://pypost.atlassian.net/browse/PYPOST-1467).
- **TD-4 — NON-BLOCKER**: Active supervisor `HEARTBEAT` watchdog to transition hung workers to
  `failed`.
  Jira: [PYPOST-1468](https://pypost.atlassian.net/browse/PYPOST-1468).
- **TD-5 — NON-BLOCKER**: Per-worker memory ceilings and spawn admission control for process-mode
  MCP workers.
  Jira: [PYPOST-1469](https://pypost.atlassian.net/browse/PYPOST-1469).
- **TD-6 — NON-BLOCKER**: Process-mode 10x multi-server stress parity and Windows stop-escalation
  CI coverage.
  Jira: [PYPOST-1470](https://pypost.atlassian.net/browse/PYPOST-1470).
