# Roadmap: PYPOST-1196

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1196/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1196/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - Red confirmed: `tests/test_mcp_server_manager.py::test_update_tools_restarts_when_stop_join_times_out`
  - Failure: `mcp_port_still_busy` then `start_failed` / EADDRINUSE (matches filed flake)
- [x] **STEP 4: Development**
  - [x] Keep `_server_thread` until not alive after join timeout
  - [x] Bump `_wait_until_port_bindable` default to 10.0s
  - [x] Harden `test_update_tools_restarts_when_exposed_set_changes` to `is_listening`
  - [x] Green: join-timeout repro + exposed-set + bindable-wait + full manager module
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1196/40-code-cleanup.md`
  - `make lint` OK
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1196/50-observability.md` — no new event names; 10s wait budget
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1196/60-tech-debt.md` — no blockers; no new follow-up tickets
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/mcp_integration.md` — 10s wait + join-timeout retain
  - Updated `doc/dev/testing.md` — PYPOST-1196 join-timeout coverage
  - Updated `doc/dev/mcp_server_registry.md` — restart path note
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1196/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1196/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1196/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1196/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1196/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
