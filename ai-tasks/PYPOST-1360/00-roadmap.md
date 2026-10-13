# Roadmap: PYPOST-1360

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_makefile_slow_smoke.py::TestSlowInstallSmoke::test_install_succeeds_with_project_pyproject`
- [x] **STEP 4: Development**
  - [x] Iteration 1: Link host site-packages in `make_workspace_full_deps` fixture via `.pth` pointer, eliminating multi-hundred MB wheel downloads and allowing slow install smoke to complete in ~11-21s.
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Technical Debt Analysis**
- [x] **STEP 8: Dev Docs**
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1360/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1360/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1360/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1360/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1360/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
