# Roadmap: PYPOST-1291

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Determine implementation language (Python)
  - [x] Gather requirements from issue description and parent task PYPOST-1285
  - [x] `ai-tasks/PYPOST-1291/10-requirements.md` drafted and accepted by review
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Research existing facades and call sites
  - [x] Implementation Plan with failing-repro design
  - [x] Mermaid architecture diagram and module responsibilities
  - [x] `ai-tasks/PYPOST-1291/20-architecture.md` accepted by review
- [x] **STEP 3: Failing Repro Test**
  - [x] Write automated red test in `tests/test_main_window_hotkeys.py` (`TestTabsPresenterDeadFacadesRemoved`)
  - [x] Verify test failure matches intended behavior (`TabsPresenter should not have dead facade method`)
  - [x] Step 3 review accepted
- [x] **STEP 4: Development**
  - [x] Remove dead facade methods from `TabsPresenter` in `pypost/ui/presenters/tabs_presenter.py`
  - [x] Update tests in `tests/test_main_window_hotkeys.py` to use `handle_f5_global` and `handle_ctrl_return_global`
  - [x] Update baseline metrics in `ai-tasks/PYPOST-376/baseline-metrics.md` (1074 -> 1053 LOC)
  - [x] Verify tests pass (`test_main_window_hotkeys.py`, `test_solid_audit_baseline.py`), `make lint`, `make typecheck`
  - [x] Step 4 review accepted
- [x] **STEP 5: Code Cleanup**
  - [x] Static analysis and formatting verified (`make lint`, all lines <= 100 chars)
  - [x] Code cleanup verified (0 unused imports, 0 debug prints)
  - [x] Test suite passing and timeout markers verified
  - [x] `ai-tasks/PYPOST-1291/40-code-cleanup.md` created
  - [x] Step 5 review accepted
- [x] **STEP 6: Observability**
  - [x] Observability requirements analyzed (dead code removal; existing structured `hotkey_routed` logging preserved)
  - [x] `ai-tasks/PYPOST-1291/50-observability.md` created
  - [x] Step 6 review accepted
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze codebase changes for technical debt, shortcuts, and missing tests
  - [x] Create `ai-tasks/PYPOST-1291/60-tech-debt.md`
  - [x] Step 7 review accepted
  - [x] Phase C blocker review accepted (SAFE TO CLOSE)
- [x] **STEP 8: Dev Docs**
  - [x] Update `doc/dev/hotkeys.md` documenting dead facade removal and unified dispatch architecture
  - [x] Step 8 review accepted
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1291/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1291/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1291/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1291/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1291/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
