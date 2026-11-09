# Roadmap: PYPOST-1541

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1541/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1541/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_mcp_live_server_port_bind_repro.py::test_live_mcp_server_starts_when_allocated_port_stolen_before_listen`
- [x] **STEP 4: Development**
  - [x] Added `allocate_bound_tcp_socket` (hold bind under flock; caller owns socket)
  - [x] Wired `LiveMCPServer` to pre-bound sockets + bind retry loop
  - [x] Kept `allocate_tcp_port` / `free_port` as thin wrappers over bound allocation
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1541/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1541/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1541/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/testing.md` — `allocate_bound_tcp_socket` / LiveMCPServer retry guidance (PYPOST-1541)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1541/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1541/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1541/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1541/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1541/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
