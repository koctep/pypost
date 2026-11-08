# Roadmap: PYPOST-1468 — Active HEARTBEAT watchdog → failed for MCP workers

## Task Metadata

- **Implementation language**: Python

## Implementation Steps

- [x] **STEP 1: Requirements Gathering**
  - Documented business goals, user stories, acceptance criteria, failure containment, and
    scope boundaries for active heartbeat watchdog in `ai-tasks/PYPOST-1468/10-requirements.md`.
- [x] **STEP 2: Architecture & Design**
  - Designed active heartbeat watchdog architecture (`McpHeartbeatPolicy`, nonce ping/pong,
    timeout detection, runaway termination, and auto-restart interplay) in
    `ai-tasks/PYPOST-1468/20-architecture.md`.
- [x] **STEP 3: Failing Repro Test**
  - Created red acceptance test suite in `tests/test_mcp_ipc_heartbeat_watchdog_repro.py`
    covering policy validation, normal roundtrip, hung timeout, disabled policy, and auto-restart.
  - Confirmed 5 cleanly failing checks in `/tmp/PYPOST-1468-step3-red.log`.
- [x] **STEP 4: Development**
  - Implemented `McpHeartbeatPolicy` model and `AppSettings.mcp_heartbeat_policy` in
    `pypost/models/settings.py`.
  - Added heartbeat tracking state, probe dispatching, `HEARTBEAT_PONG` handling, and watchdog
    timeout escalation to `pypost/core/mcp_process_supervisor.py`.
  - Propagated `heartbeat_policy` through `MCPServerRegistry`, `McpServerSettingsController`,
    and `DaemonRuntime`.
  - Verified green pass across all 5 acceptance tests in
    `tests/test_mcp_ipc_heartbeat_watchdog_repro.py` and regression suites.
- [x] **STEP 5: Code Cleanup**
  - Audited code formatting, docstrings, and imports across all touched production and test files.
  - Verified every line in touched files and artifacts is strictly <= 100 characters.
  - Confirmed explicit `@pytest.mark.timeout(...)` markers and module timeouts per `do-testing`.
  - Documented cleanup and quality gates in `ai-tasks/PYPOST-1468/40-code-cleanup.md`.
- [x] **STEP 6: Observability**
  - Documented structured logging (`mcp_worker_heartbeat_timeout`, `mcp_worker_heartbeat_pong`,
    `mcp_worker_heartbeat_pong_mismatch`, `mcp_worker_restart_scheduled`) in
    `ai-tasks/PYPOST-1468/50-observability.md`.
  - Added caplog test coverage for structured watchdog timeout, pong debug, and mismatch warning
    logs in `tests/test_mcp_ipc_heartbeat_watchdog_repro.py`.
  - Verified secret safety, performance metrics, and system health status tracking.
- [x] **STEP 7: Technical Debt Analysis**
  - Evaluated shortcuts (synchronous pipe send, single probe, fixed kill escalation delay),
    modularization, and low performance overhead in `ai-tasks/PYPOST-1468/60-tech-debt.md`.
  - Confirmed zero missing tests and full compliance with `do-testing` timeout markers.
  - Triaged pre-existing lint failure `tests/test_mcp_server_registry.py:308:101: E501` as
    `NON-BLOCKER - pre-existing` under [PYPOST-1509](
    https://pypost.atlassian.net/browse/PYPOST-1509).
  - Verified 0 blockers; received `SAFE TO CLOSE (PASS)`.
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/mcp_process_isolation.md` to document the active HEARTBEAT watchdog.
  - Documented `McpHeartbeatPolicy` configuration, defaults, bounds, and code sample.
  - Documented nonce ping/pong protocol exchange (`HEARTBEAT` / `HEARTBEAT_PONG`).
  - Documented `_monitor_loop` probe scheduling, timeout detection, and kill escalation.
  - Documented auto-restart interplay and structured observability log events.
  - Added reproduction test commands and acceptance criteria summary.
  - Verified every line in `doc/dev/mcp_process_isolation.md` is strictly <= 100 characters.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1468/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1468/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_mcp_ipc_heartbeat_watchdog_repro.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1468/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1468/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1468/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
