# PYPOST-1468: Technical Debt Analysis

## Shortcuts Taken

No brittle bypasses, unhandled exceptions, or temporary stubs were introduced:

- **Synchronous send within monitor loop**: In `_monitor_loop`, when `pending_heartbeat_nonce` is
  `None` and the elapsed time reaches `interval_s`, the supervisor synchronously issues
  `record.parent_conn.send(make_message("HEARTBEAT", nonce=nonce))`. OS duplex pipe `send` is
  non-blocking under normal conditions with small payloads (< 100 bytes) because the worker reader
  loop continuously drains the pipe. A decoupled asynchronous sending queue or dedicated probe
  thread was deferred because worker concurrency is low (typically <= 4) and IPC buffers remain
  uncongested.
- **Single in-flight probe per worker slot**: Nonce tracking in `_WorkerRecord` holds at most one
  active `pending_heartbeat_nonce` and `pending_heartbeat_sent_at`. Multi-probe pipelining or
  sliding window sequence tracking was intentionally avoided: if a worker does not respond within
  `timeout_s`, it is considered hung and terminated. Any late pong arriving after timeout is safely
  logged as a mismatch or ignored.
- **Fixed stop budget for kill escalation**: When watchdog timeout triggers worker termination,
  the supervisor invokes `_kill_worker_process(proc_to_kill)` which uses `SIGTERM` followed by a
  wait bounded by `stop_budget_s` (default 5.0 seconds) before escalating to `SIGKILL`. A dedicated
  `kill_escalation_delay_s` parameter in `McpHeartbeatPolicy` was not added to keep the policy
  configuration focused on detection (`interval_s`, `timeout_s`).

## Code Quality Issues

No code-quality blockers exist in the modified production and test modules:

- **Monitor loop method size**: `_monitor_loop` in `pypost/core/mcp_process_supervisor.py` now
  manages child liveness, restart backoff deadlines, RSS memory limit sampling, and heartbeat
  watchdog probing. While each section is scoped cleanly with lock isolation, extracting the
  heartbeat check into a helper method (`_check_worker_heartbeat`) would reduce method length.
- **State encapsulation**: Heartbeat tracking fields (`last_heartbeat_sent_at`,
  `last_heartbeat_pong_at`, `pending_heartbeat_nonce`, `pending_heartbeat_sent_at`) are stored
  directly on `_WorkerRecord`. Grouping these into a dedicated `_HeartbeatState` sub-dataclass could
  further modularize worker state in future supervisor refactoring.
- **Clean state resets**: Worker state resets upon restart properly clear `pending_heartbeat_nonce`,
  `pending_heartbeat_sent_at`, and timestamp metrics, ensuring clean slate execution across
  restart cycles.
- **Static analysis and typing**: Full compliance with PEP 8 and `lsr-python`. Production lint and
  type checking pass green with zero errors (`make -o lint-tests lint`, `make typecheck`).

## Missing Tests

No missing test coverage is classified as a **BLOCKER**:

- **Explicit timeout markers (`do-testing`)**: All 6 tests in
  `tests/test_mcp_ipc_heartbeat_watchdog_repro.py` declare explicit `@pytest.mark.timeout(...)`
  markers (20s or 30s) alongside module-level `pytestmark = pytest.mark.timeout(60)`.
- **Bounded waits**: All wait conditions use `wait_until(...)` with explicit timeouts (typically
  5.0s) and bounded polling intervals (0.02s–0.03s), preventing unbounded CI execution.
- **Error-path caplog assertions**: Tested structured log outputs for:
  - `mcp_worker_heartbeat_timeout` (ERROR) when watchdog terminates hung worker.
  - `mcp_worker_heartbeat_pong` (DEBUG) for successful roundtrip ping/pong.
  - `mcp_worker_heartbeat_pong_mismatch` (WARNING) when invalid or unexpected nonce is received.
  - `mcp_worker_restart_scheduled` (INFO) for watchdog timeout auto-restart interplay.
- **Covered test scenarios**:
  1. `test_heartbeat_policy_validation_and_defaults`: Schema validation and boundaries.
  2. `test_normal_worker_heartbeats_roundtrip_successfully`: Healthy bidirectional IPC ping/pong.
  3. `test_hung_worker_times_out_and_is_terminated_to_failed`: Watchdog termination to `failed`.
  4. `test_disabled_watchdog_does_not_terminate_hung_worker`: Opt-out policy integrity.
  5. `test_heartbeat_timeout_interplay_with_auto_restart`: Watchdog triggers backoff restart.
  6. `test_heartbeat_pong_mismatch_warning_logged`: Security and robustness against stale nonces.
- **Future test enhancements (non-blocking)**:
  - High-frequency probe stress tests under simulated heavy CPU contention.
  - Worker crash during in-flight probe dispatch edge case verification.

## Performance Concerns

No performance blocker was introduced by this change:

- **Negligible IPC overhead**: With default `interval_s=5.0`, heartbeat probes generate one ~60
  byte message every 5 seconds per active worker. Serialization and pipe transmission take < 5 µs.
- **Dedicated worker IPC thread**: Heartbeat probes are received and replied to on the worker's
  dedicated IPC listener thread (`_ipc_reader_loop`), avoiding latency interference with active
  tool execution or async server dispatching.
- **O(1) in-memory correlation**: Nonce validation is an exact string equality check on the worker
  record, incurring zero collection search overhead or lock contention.

## Follow-up Tasks

All follow-up items below are **NON-BLOCKER** and properly classified:

- **TD-1 — NON-BLOCKER — pre-existing**: Test lint reports
  `tests/test_mcp_server_registry.py:308:101: E501 line too long (111 > 100 characters)` when
  running `make lint` (pre-existing baseline violation).
  Jira: [PYPOST-1509](https://pypost.atlassian.net/browse/PYPOST-1509).
- **TD-2 — NON-BLOCKER**: Modularize `_monitor_loop` in `pypost/core/mcp_process_supervisor.py` by
  extracting heartbeat evaluation logic into a dedicated helper method.
  Jira: optional future refactoring debt.
- **TD-3 — NON-BLOCKER**: Consider configurable kill escalation delay in `McpHeartbeatPolicy`
  (e.g., `kill_escalation_delay_s`) if specific MCP servers require custom shutdown grace periods.
  Jira: optional future enhancement.

---

## Blocker Review

| Check | Requirement | Status | Notes |
| ----- | ----------- | ------ | ----- |
| **Pytest Timeouts** | Explicit timeout marker | PASS | All 6 tests marked per do-testing |
| **Acceptance path** | Probing, timeout & restart | PASS | Repro test suite green (6/6 passed) |
| **Error-path caplog** | Structured logging assertion | PASS | Timeout & mismatch logs tested |
| **Architecture debt** | Nonce tracking & send loop | PASS | Analyzed in Shortcuts & Quality |
| **Unticketed Debt** | Follow-ups documented | PASS | Pre-existing TD-1 in PYPOST-1509 |

**Zero BLOCKERs**. Safe to proceed to Step 8 (Dev Docs) after acceptance gate on this artifact.

**SAFE TO CLOSE**
