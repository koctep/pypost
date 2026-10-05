# Roadmap: PYPOST-1294

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Determine implementation language (Python)
  - [x] Gather requirements from issue description and parent task PYPOST-1285
  - [x] `ai-tasks/PYPOST-1294/10-requirements.md` drafted and accepted by review
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Research `_keys_from_action`, `tag_action`, `register_hotkey_group`, and `_EXPECTED_OTHER_HELP_ROWS`
  - [x] Design centralized NativeText formatting in `pypost/ui/hotkeys.py` and test snapshot normalization
  - [x] Implementation Plan with failing-repro design for Step 3
  - [x] `ai-tasks/PYPOST-1294/20-architecture.md` accepted by review
- [x] **STEP 3: Failing Repro Test**
  - [x] Write failing repro test in `tests/test_hotkeys.py` (`test_collect_hotkey_rows_formats_all_keys_with_native_text`)
  - [x] Verify automated failure reproduces the deficiency (raw alt key string returned without NativeText)
  - [x] Step 3 review accepted
- [x] **STEP 4: Development**
  - [x] Normalize all keys in `_keys_from_action` in `pypost/ui/hotkeys.py` via `NativeText`
  - [x] Normalize keys comparison in `tag_action` in `pypost/ui/hotkeys.py`
  - [x] Transform `_EXPECTED_OTHER_HELP_ROWS` in `tests/test_main_window_hotkeys.py` to platform-neutral native text
  - [x] Verify Step 3 test passes green and test suites pass
  - [x] Step 4 review accepted
- [x] **STEP 5: Code Cleanup**
  - [x] Static analysis and formatting verified (`make lint`, all lines <= 100 chars)
  - [x] Code cleanup verified (0 unused imports, 0 debug prints)
  - [x] Test suite passing and timeout markers verified
  - [x] `ai-tasks/PYPOST-1294/40-code-cleanup.md` created
  - [x] Step 5 review accepted
- [x] **STEP 6: Observability**
  - [x] Analyze observability requirements (Help UI shortcut formatting; no production logging impact)
  - [x] Create `ai-tasks/PYPOST-1294/50-observability.md`
  - [x] Step 6 review accepted
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze codebase changes for technical debt, shortcuts, and missing tests
  - [x] Create `ai-tasks/PYPOST-1294/60-tech-debt.md`
  - [x] Step 7 review accepted
  - [x] Phase C blocker review accepted (SAFE TO CLOSE)
- [x] **STEP 8: Dev Docs**
  - [x] Update `doc/dev/hotkeys.md` to document platform-neutral NativeText key display formatting
  - [x] Step 8 review accepted
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1294/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1294/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1294/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1294/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1294/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
