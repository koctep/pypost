# Roadmap: PYPOST-1508

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1508/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1508/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_mcp_process_isolation_port_hold_repro.py::test_batch_ports_stay_held_across_all_multi_server_setup_steps`
  - Red evidence: early `release()` after first setup step → reuse-addr thief bind succeeds → `Failed: DID NOT RAISE OSError`
- [x] **STEP 4: Development**
  - [x] Removed early `release()` anti-pattern from multi-step hold repro
  - [x] `test_process_mode_variable_isolation_under_concurrent_load`: hold through all upserts; single `reserve.release()` then start all
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1508/40-code-cleanup.md`
  - `make lint` pass
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1508/50-observability.md` (reuse PYPOST-1546 DEBUG allocate/release)
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1508/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/testing.md` — hold-through-all-upserts (PYPOST-1508)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1508/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1508/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1508/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1508/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1508/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
