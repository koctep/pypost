# Roadmap: PYPOST-1362

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1362/10-requirements.md`
  - Language: Python
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1362/20-architecture.md`
  - Failing-repro plan: assert `_server_thread is None` after failed bind + worker exit
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_mcp_server_registry.py::test_failed_bind_clears_server_thread_after_worker_exits`
  - Red confirmed: retained stopped Thread after worker exit; isolation test adds bounded wait
- [x] **STEP 4: Development**
  - [x] Clear `_server_thread` on worker exit in `_run_uvicorn` (current_thread guard)
  - [x] `stop_server` joins via local thread snapshot (avoid None race)
  - [x] `_wait_until_not_running` + harden `test_failed_bind_is_reported_for_only_the_requested_instance`
  - [x] Red test green; registry + adaptive_join suites green
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1362/40-code-cleanup.md`
  - `make lint` OK; E501 fixed on wait helper
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1362/50-observability.md`
  - N/A new logs — retained existing `mcp_server_start_failed` / registry status
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1362/60-tech-debt.md`
  - No Jira follow-ups created (task instruction)
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/mcp_concurrent_multiserver.md`, `mcp_integration.md`, `collection_scoped_variables.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1362/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1362/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_mcp_server_registry.py::test_failed_bind_clears_server_thread_after_worker_exits`

### STEP 4: Development

- `pypost/core/qt/mcp_server.py`
- `tests/test_mcp_server_registry.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1362/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1362/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1362/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_concurrent_multiserver.md`
- `doc/dev/mcp_integration.md`
- `doc/dev/collection_scoped_variables.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
