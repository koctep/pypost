# Roadmap: PYPOST-1493

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1493/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1493/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_mcp_stdio_harness.py::test_harness_stderr_visible_when_emitted_after_response`
  - Red confirmed: empty `get_stderr()` after `wait_for_response` when child emits stderr post-response (`AssertionError`)
- [x] **STEP 4: Development**
  - [x] Added `McpStdioHarness.wait_for_stderr` + stderr-worker `notify_all`
  - [x] Stabilized `test_harness_stderr_collection` via `wait_for_stderr`
  - [x] Greened `test_harness_stderr_visible_when_emitted_after_response`
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1493/40-code-cleanup.md`
  - `make lint` pass
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1493/50-observability.md`
  - DEBUG ready / WARNING timeout on `wait_for_stderr`
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1493/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/mcp_standalone_wire_ipc_stress.md` (`wait_for_stderr` + troubleshooting)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1493/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1493/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1493/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1493/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1493/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
