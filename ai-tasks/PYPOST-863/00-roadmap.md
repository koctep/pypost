# Roadmap: PYPOST-863

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *tests/test_agent_e2e_seed.py — drive-then-snapshot / resolve proof*
- [x] **STEP 4: Development**
  - [x] Added `tests/helpers/agent_e2e_tree.py` (viewport visualRect click)
  - [x] Added `test_seed_drive_then_snapshot_active_env_and_open_get` (green;
    no production code change — coverage debt)
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python 3.10+ (pytest agent e2e; Markdown for `doc/dev`)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-863/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-863/20-architecture.md`

### STEP 3: Failing Repro

- Automated red/acceptance test under `tests/` (or N/A note)

### STEP 4: Development

- Source code / tests / docs updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-863/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-863/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-863/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`
