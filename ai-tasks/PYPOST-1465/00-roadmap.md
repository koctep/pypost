# Roadmap: PYPOST-1465

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Business purpose established by the approved MCP Process Reliability sprint and deferred collection tool-refresh parity from PYPOST-1439.
  - Requirements documented in `ai-tasks/PYPOST-1465/10-requirements.md` covering live collection updates for isolated servers, variable privacy, neighboring server isolation, and shared-mode compatibility.
- [x] **STEP 2: High-Level Architecture Design**
  - Architecture documented in `ai-tasks/PYPOST-1465/20-architecture.md`.
  - Designed zero-downtime process-mode collection refresh via `UPDATE_TOOLS` and `UPDATE_VARIABLES` IPC messages, runner protocol parity (`update_tools`), snapshot consistency on `ProcessServerRunner`, and failure-contained registry dispatch across workspace and library-backed local servers.
- [x] **STEP 3: Failing Repro Test**
  - Test file: `tests/test_mcp_process_tool_refresh_repro.py`
  - Command: `make test WORKERS=1 PYTEST_ARGS='tests/test_mcp_process_tool_refresh_repro.py -q'` (log saved to `/tmp/PYPOST-1465-step3-red.log`)
  - Red failure evidence (5 failed):
    - `test_process_mode_refresh_collection_updates_tools_live_add_modify_remove` — `AssertionError: Timed out waiting for process worker tools/list update after 2.0s`
    - `test_process_mode_refresh_collection_updates_collection_variables_and_preserves_env` — `AssertionError: Timed out waiting for workspace collection variable refresh in process worker after 2.0s`
    - `test_process_mode_refresh_collection_isolates_neighbor_and_proxy_servers` — `AssertionError: Timed out waiting for target collection server tool refresh after 2.0s`
    - `test_process_mode_refresh_collection_contains_exited_worker_and_updates_snapshot` — `AssertionError: Timed out waiting for healthy peer tools/list refresh after 2.0s`
    - `test_shared_mode_refresh_collection_regression_parity` — `AssertionError: Timed out waiting for thread-mode in-place tool description refresh after 2.0s`
- [x] **STEP 4: Development**
  - [x] Iteration 1: Added `UPDATE_TOOLS` IPC message schema (`pypost/core/mcp_worker_ipc.py`), atomic `MCPServerImpl.register_tools` map replacement (`pypost/core/mcp_server_impl.py`), worker `UPDATE_TOOLS` handler (`pypost/core/mcp_worker_process.py`), and failure-contained `McpProcessSupervisor.update_tools` (`pypost/core/mcp_process_supervisor.py`).
  - [x] Iteration 2: Added `update_tools` to `MCPServerRunnerProtocol`, `ThreadServerRunner`, and `ProcessServerRunner` with `_spec` snapshot synchronization (`pypost/core/mcp_server_runner.py`), and ensured `MCPServerManager.update_tools` refreshes in-place request modifications (`pypost/core/qt/mcp_server.py`).
  - [x] Iteration 3: Unified `MCPServerRegistry.refresh_collection` and workspace variable merging across process and thread execution modes for both workspace-backed and library-backed local servers with dead-worker failure containment (`pypost/core/mcp_server_registry.py`).
  - Artifacts: `pypost/core/mcp_worker_ipc.py`, `pypost/core/mcp_server_impl.py`, `pypost/core/mcp_worker_process.py`, `pypost/core/mcp_process_supervisor.py`, `pypost/core/mcp_server_runner.py`, `pypost/core/qt/mcp_server.py`, `pypost/core/mcp_server_registry.py`, `tests/test_mcp_process_tool_refresh_repro.py`
- [x] **STEP 5: Code Cleanup**
  - Artifact: `ai-tasks/PYPOST-1465/40-code-cleanup.md`
  - Sorted imports in `tests/test_mcp_process_tool_refresh_repro.py` and verified PEP 8 formatting (<= 100 chars), absence of unused imports/variables or dead code, and explicit `@pytest.mark.timeout(60)` markers across all modified files.
  - Verified quality gates via `make -o lint-tests lint`, `make typecheck`, and `make test WORKERS=1 PYTEST_ARGS='tests/test_mcp_process_tool_refresh_repro.py -q'`.
- [x] **STEP 6: Observability**
  - Artifact: `ai-tasks/PYPOST-1465/50-observability.md`
  - Added structured, secret-safe observability across `pypost/core/mcp_process_supervisor.py` (`mcp_worker_update_tools_sent`, `mcp_worker_ipc_ack`, `mcp_worker_ipc_error`), `pypost/core/mcp_worker_process.py` (exception-class-only `mcp_worker_update_tools_failed`), and `pypost/core/mcp_server_registry.py` (`mcp_registry_collection_refreshed` with counts only).
  - Extended `tests/test_mcp_process_tool_refresh_repro.py` with `caplog` assertions verifying lifecycle/error log events and confirming `UPDATE_TOOLS` / `UPDATE_VARIABLES` payloads and secret values are never logged.
- [x] **STEP 7: Technical Debt Analysis**
  - Artifact: `ai-tasks/PYPOST-1465/60-tech-debt.md`
  - Evaluated shortcuts taken, code quality, test coverage (including explicit 60s timeout markers across all 5 tests in `tests/test_mcp_process_tool_refresh_repro.py`), and performance characteristics; linked pre-existing test lint (`PYPOST-1509`) and remaining process-mode sprint follow-ups (`PYPOST-1466` through `PYPOST-1470`) with zero blockers.
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/mcp_process_isolation.md` and `doc/dev/mcp_server_registry.md` with process-mode and thread-mode collection tool/variable refresh architecture, `UPDATE_TOOLS` IPC contract, runner and supervisor `update_tools` semantics, atomic `MCPServerImpl.register_tools` map replacement, in-place `MCPServerManager.update_tools` refresh, observability logs, troubleshooting, and verification test commands (`tests/test_mcp_process_tool_refresh_repro.py`).
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1465/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1465/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1465/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1465/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1465/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
