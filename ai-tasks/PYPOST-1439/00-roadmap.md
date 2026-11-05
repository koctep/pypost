# Roadmap: PYPOST-1439

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1439/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1439/20-architecture.md`
  - Runners: `MCPServerRunnerProtocol` + Thread/Process; `McpProcessSupervisor` (spawn);
    headless `mcp_worker_process`; IPC START/UPDATE_VARIABLES/HEARTBEAT/STOP;
    SIGTERM→SIGKILL ~2s; `mcp_execution_mode`; Step 3 red-test plan
  - Awaiting acceptance gate (do not mark `[x]` until review PASS)
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_mcp_process_isolation_repro.py`
    - `test_process_mode_setting_defaults_to_thread_and_accepts_process` (red: missing setting)
    - `test_process_mode_crash_isolation_peer_servers_survive` (red: missing process path)
    - `test_process_mode_variable_isolation_under_concurrent_load` (red: missing process path)
    - `test_process_mode_bounded_stop_with_unresponsive_worker` (red: missing process path)
    - `test_thread_mode_regression_still_passes_10x_barrier_startup` (green control: default harness, no new API)
- [x] **STEP 4: Development**
  - [x] Marked STEP 4 in progress; began Phase 2 process-mode implementation
  - [x] Added `AppSettings.mcp_execution_mode` (`thread`/`process`, default `thread`)
  - [x] Added `mcp_worker_ipc.py`, `mcp_worker_process.py`, `mcp_process_supervisor.py`,
    `mcp_server_runner.py` (protocol + Thread/Process runners)
  - [x] Wired `MCPServerRegistry(execution_mode=...)`, `runner_for()`, process start/stop,
    unexpected child exit → `failed`; thread mode unchanged
  - [x] Test echo gate `PYPOST_MCP_TEST_ECHO_VARS=1` for cross-process variable isolation;
    adjusted isolation repro to set env before spawn (removed ineffective parent patch)
  - [x] `make test PYTEST_ARGS="tests/test_mcp_process_isolation_repro.py -v"` GREEN (5 passed)
  - [x] MCP 10x stress smoke GREEN (`tests/test_mcp_multiserver_stress_10x.py`, 4 passed)
  - [x] Review FAIL fix: dedicated per-worker IPC reader (no shared Pipe drain /
    poll→recv race; never join reader under process-table lock)
  - [x] Review FAIL fix: lazy-import Qt `WebSocketProbeRunner` in
    `websocket_mcp_tools.execute_websocket_probe` so worker import graph excludes PySide6
  - [x] Review FAIL fix: gate `DEBUG_ABORT`/`DEBUG_HANG` on
    `PYPOST_MCP_ALLOW_DEBUG_IPC=1` (supervisor reject + worker ignore); isolation tests set env
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1439/40-code-cleanup.md`
  - mypy: setattr for uvicorn hooks in `mcp_worker_process`; narrowed runner/registry types
  - `make lint` OK; `make typecheck` OK (baseline 175)
  - Isolation repro GREEN (`tests/test_mcp_process_isolation_repro.py`)
  - Awaiting acceptance gate (do not mark `[x]` until review PASS)
- [x] **STEP 6: Observability**
  - Extended structured logs: `mcp_registry_execution_mode_selected`,
    `mcp_worker_spawned` / `mcp_worker_started` / `mcp_worker_start_failed`,
    `mcp_worker_unexpected_exit` + `mcp_registry_unexpected_child_exit` → `failed`,
    `mcp_worker_stop_requested` / `mcp_worker_terminate` (SIGTERM) /
    `mcp_worker_kill` (SIGKILL) / `mcp_worker_stop_finished`
  - Metrics: reuse `_publish_instance_metrics` / `mcp_server_instances` on status transitions
  - Artifact: `ai-tasks/PYPOST-1439/50-observability.md`
  - `make test PYTEST_ARGS="tests/test_mcp_process_isolation_repro.py -v"` GREEN
  - Awaiting acceptance gate (do not mark `[x]` until review PASS)
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1439/60-tech-debt.md`
  - Follow-ups UNTICKETED (no Jira create per parent run)
  - Review FAIL fix: wire `AppSettings.mcp_execution_mode` into
    `MCPServerRegistry(..., execution_mode=...)` in `mcp_server_controller` +
    `daemon_runtime`; Settings UI remains NON-BLOCKER TD-1
  - Zero BLOCKERs after wiring fix; High/Med/Low NON-BLOCKER drafts with Fibonacci SP
  - Awaiting acceptance gate (do not mark `[x]` until review PASS)
- [x] **STEP 8: Dev Docs**
  - Created `doc/dev/mcp_process_isolation.md` (execution mode, supervisor/worker/IPC,
    DEBUG/`TEST_ECHO` gates, STOP→SIGTERM→SIGKILL, troubleshooting, tests)
  - Updated `doc/dev/mcp_process_supervisor_evaluation.md` Phase 2 → implemented (PYPOST-1439)
  - Cross-linked process mode from `doc/dev/mcp_concurrent_multiserver.md`
  - TOC: `doc/dev/README.md`; task summary: `ai-tasks/PYPOST-1439/70-dev-docs.md`
  - Awaiting acceptance gate (do not mark `[x]` until review PASS)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1439/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1439/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1439/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1439/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1439/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_process_isolation.md`
- `doc/dev/mcp_process_supervisor_evaluation.md` (Phase 2 status)
- `doc/dev/mcp_concurrent_multiserver.md` (cross-link)
- `doc/dev/README.md`
- `ai-tasks/PYPOST-1439/70-dev-docs.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
