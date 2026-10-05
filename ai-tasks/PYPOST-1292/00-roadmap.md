# Roadmap: PYPOST-1292

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Determine implementation language (Python)
  - [x] Gather requirements from issue description and parent task PYPOST-1285
  - [x] `ai-tasks/PYPOST-1292/10-requirements.md` drafted and accepted by review
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Research existing duplicated window activation logic in `test_hotkeys.py` and `test_main_window_hotkeys.py`
  - [x] Design shared helper module `tests/helpers/qt_activation.py` and failing repro plan
  - [x] Create Mermaid architecture diagram and document module responsibilities
  - [x] `ai-tasks/PYPOST-1292/20-architecture.md` accepted by review
- [x] **STEP 3: Failing Repro Test**
  - [x] Write automated red test `tests/test_qt_activation_helper.py`
  - [x] Verify test failure matches intended missing behavior (`ModuleNotFoundError: No module named 'tests.helpers.qt_activation'`)
  - [x] Step 3 review accepted
- [x] **STEP 4: Development**
  - [x] Create shared helper `tests/helpers/qt_activation.py` with `ACTIVATION_SKIP`, `activate_window`, `click_key`, and `ActivatedWindow`
  - [x] Verify `tests/test_qt_activation_helper.py` passes green
  - [x] Refactor `tests/test_hotkeys.py` to use `ActivatedWindow`
  - [x] Refactor `tests/test_main_window_hotkeys.py` to use `activate_window` and `click_key`
  - [x] Verify all test suites pass, `make lint` and `make typecheck` pass
  - [x] Step 4 review accepted
- [x] **STEP 5: Code Cleanup**
  - [x] Static analysis and formatting verified (`make lint`, all lines <= 100 chars)
  - [x] Code cleanup verified (0 unused imports, 0 debug prints)
  - [x] Test suite passing and timeout markers verified
  - [x] `ai-tasks/PYPOST-1292/40-code-cleanup.md` created
  - [x] Step 5 review accepted
- [x] **STEP 6: Observability**
  - [x] Observability requirements analyzed (test-only helper extraction, no production logging impact)
  - [x] `ai-tasks/PYPOST-1292/50-observability.md` created
  - [x] Step 6 review accepted
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze codebase changes for technical debt, shortcuts, and missing tests
  - [x] Create `ai-tasks/PYPOST-1292/60-tech-debt.md`
  - [x] Step 7 review accepted
  - [x] Phase C blocker review accepted (SAFE TO CLOSE)
- [x] **STEP 8: Dev Docs**
  - [x] Create `doc/dev/qt_activation_helper.md`
  - [x] Link helper in `doc/dev/hotkeys.md`
  - [x] Step 8 review accepted
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1292/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1292/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1292/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1292/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1292/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
