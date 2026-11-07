# PYPOST-1466: Technical Debt Analysis

## Shortcuts Taken

No temporary stubs, bypasses, or hardcoded workarounds remain in the auto-restart implementation:

- **Single global policy configuration**: `AppSettings.mcp_restart_policy` provides a unified
  restart policy model (`McpWorkerRestartPolicy`) applied across all isolated MCP workers.
  Per-server policy overrides were not introduced as the current product architecture defines
  MCP runtime settings globally at host startup.
- **Settings UI dialog control deferred**: `McpWorkerRestartPolicy` is fully wired from
  persisted `AppSettings` through `McpServerSettingsController`, `DaemonRuntime`,
  `MCPServerRegistry`, and `McpProcessSupervisor`. The Settings dialog widget controls for both
  `mcp_execution_mode` and `mcp_restart_policy` are tracked under the dedicated UI task
  ([PYPOST-1462](https://pypost.atlassian.net/browse/PYPOST-1462)).
- **Ephemeral in-memory retry tracking**: Consecutive retry counts and monotonic backoff
  deadlines are maintained in memory within `_WorkerRecord` during the supervisor's active
  lifespan. If the host application exits or terminates, retry counters reset cleanly on the next
  startup. This matches the existing in-process lifecycle design of `McpProcessSupervisor`.
- **Immediate backoff cancellation**: Explicit operator lifecycle actions (`stop_worker`,
  `reconfigure`, `shutdown`) signal a dedicated cancellation event (`cancel_event`) rather than
  blocking or sleeping through the remaining backoff interval, ensuring bounded stop times.

## Code Quality Issues

No code-quality blocker was identified across the modified modules (`pypost/models/settings.py`,
`pypost/core/mcp_process_supervisor.py`, `pypost/core/mcp_server_runner.py`,
`pypost/core/mcp_server_registry.py`, `pypost/core/mcp_worker_process.py`,
`pypost/ui/mcp_server_controller.py`, `pypost/core/qt/daemon_runtime.py`, and
`tests/test_mcp_process_autorestart_repro.py`):

- **Clean policy encapsulation**: Backoff delay computation is strictly encapsulated inside
  `McpWorkerRestartPolicy.backoff_for_attempt(attempt)` with Pydantic field bounds validation
  preventing negative or zero multipliers and invalid retry ceilings.
- **State preservation during backoff**: `ProcessServerRunner` retains and mutates `_spec`
  (`_WorkerSpawnSpec`) during live tool additions (`update_tools`) and environment variable
  updates (`update_variables`), guaranteeing that subsequent respawns after backoff restore the
  latest tools, variables, and proxy settings.
- **Non-blocking supervisor scheduling**: Monotonic deadlines prevent worker monitor threads from
  blocking concurrent operations, while the supervisor thread safely inspects deadlines on 50 ms
  polling intervals.
- **Static analysis and typing**: Production and Markdown lint (`make -o lint-tests lint`) and
  `make typecheck` pass with zero new warnings or errors. Test lint has only the pre-existing E501
  violation in `tests/test_mcp_server_registry.py:308:101` tracked under
  [PYPOST-1509](https://pypost.atlassian.net/browse/PYPOST-1509).

## Missing Tests

No missing test coverage is classified as a **BLOCKER**:

- **Timeout markers**: `tests/test_mcp_process_autorestart_repro.py` declares both a module-level
  `pytestmark = pytest.mark.timeout(60)` and explicit per-test `@pytest.mark.timeout(...)`
  markers (20s, 30s, or 60s) across all 7 tests, fulfilling repository pytest timeout rules.
- **Covered scenarios**: The acceptance suite verifies:
  1. Policy defaults, Pydantic bounds validation, and host wiring from `AppSettings`.
  2. Default disabled policy (`enabled=False`) immediate failure without retry (`FR1`).
  3. Opt-in exponential backoff recovery preserving updated tools, variables, and proxy config
     (`FR2`, `FR5`).
  4. Retry exhaustion transitioning to terminal `failed` state after `max_retries` (`FR3`).
  5. Healthy stability window resetting consecutive retry counter (`FR4`).
  6. Immediate cancellation of pending backoff on operator stop and shutdown (`FR6`).
  7. Initial startup bind failure failing immediately without entering auto-restart loop (`FR7`).
  8. Structured key-value logging and secret-safe parameter suppression (`FR8`).
  9. Shared thread-mode regression parity control.
- **Broader stress, IPC negotiation, and watchdog CI**:
  - IPC version negotiation and mismatch rejection remain tracked under
    [PYPOST-1467](https://pypost.atlassian.net/browse/PYPOST-1467).
  - Active heartbeat watchdog liveness probing remains tracked under
    [PYPOST-1468](https://pypost.atlassian.net/browse/PYPOST-1468).
  - Process-mode 10x multi-server stress parity and Windows stop escalation CI remain tracked under
    [PYPOST-1470](https://pypost.atlassian.net/browse/PYPOST-1470).

## Performance Concerns

No new performance blocker was introduced by this task:

- **Minimal monitor loop overhead**: The supervisor monitor thread inspects deadline timestamps
  and sleeps in 50 ms intervals, consuming negligible CPU overhead while waiting for backoff
  deadlines to elapse.
- **Bounded exponential backoff**: Delays grow progressively by `backoff_multiplier` and are
  strictly capped at `max_backoff_s` (default 8.0s), preventing tight crash loops without
  introducing unbounded recovery latency.
- **Process memory ceilings**: Per-worker memory ceilings and spawn admission control for dense
  process-mode configurations remain tracked under
  [PYPOST-1469](https://pypost.atlassian.net/browse/PYPOST-1469).

## Follow-up Tasks

All follow-up items below are **NON-BLOCKER** and already tracked in Jira:

- **TD-1 — NON-BLOCKER — pre-existing**: Test lint reports
  `tests/test_mcp_server_registry.py:308:101: E501 line too long (111 > 100 characters)` when
  running `make lint` (reproduced at base commit `33d5cb1a`).
  Jira: [PYPOST-1509](https://pypost.atlassian.net/browse/PYPOST-1509).
- **TD-2 — NON-BLOCKER**: Settings UI dialog controls for `mcp_execution_mode` and
  `mcp_restart_policy`.
  Jira: [PYPOST-1462](https://pypost.atlassian.net/browse/PYPOST-1462).
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

---

## Blocker Review

| Check | Requirement | Status | Notes |
| ----- | ----------- | ------ | ----- |
| **Pytest Timeouts** | Explicit timeout marker | PASS | 7 repro tests marked with timeouts |
| **Acceptance path** | Backoff / exhaustion / stop | PASS | Repro suite green (7/7 passed) |
| **Thread regression** | NFR5 lightweight mode | PASS | Thread mode regression control green |
| **Architecture debt called out** | UI, IPC, heartbeat, memory | PASS | Follow-ups in NON-BLOCKER |
| **FR1 durable setting -> registry** | Persisted policy at host | PASS | Wired via AppSettings |
| **FR1 Settings UI** | Operator-selectable control | GAP -> TD-2 | NON-BLOCKER; in PYPOST-1462 |
| **Unticketed Debt** | Follow-ups documented | PASS | All ticketed (PYPOST-1462, 1467-1470) |

**Zero BLOCKERs**. Safe to proceed to Step 8 (Dev Docs) after acceptance gate on this artifact.

**SAFE TO CLOSE**
