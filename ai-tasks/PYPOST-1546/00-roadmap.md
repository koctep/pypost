# Roadmap: PYPOST-1546

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1546/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1546/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_ephemeral_port_reserve_hold_repro.py::test_reserve_ephemeral_ports_holds_exclusively_against_reuseaddr_thief`
  - Red evidence: `Failed: DID NOT RAISE OSError` (port free after allocate-then-release)
- [x] **STEP 4: Development**
  - [x] `allocate_bound_tcp_socket(..., reuse_addr=False)` for exclusive holds
  - [x] `EphemeralPorts` / `EphemeralPortReserve.release()` handoff API
  - [x] Process-mode suites release immediately before server start
  - [x] Green: hold repro + neighbor isolation + related process suites
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1546/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1546/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1546/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/testing.md` — exclusive hold + release handoff (PYPOST-1546)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1546/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1546/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_ephemeral_port_reserve_hold_repro.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1546/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1546/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1546/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
