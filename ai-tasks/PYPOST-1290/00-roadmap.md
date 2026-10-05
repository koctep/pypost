# Roadmap: PYPOST-1290

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Determine implementation language (Python)
  - [x] Gather requirements from issue description and parent task PYPOST-1285
  - [x] `ai-tasks/PYPOST-1290/10-requirements.md` drafted and accepted by review
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1290/20-architecture.md` drafted and accepted by review
- [x] **STEP 3: Failing Repro Test**
  - [x] Red tests for window-wide unique shortcut guard and ambiguous activation logging in tests/test_main_window_hotkeys.py accepted by review
- [x] **STEP 4: Development**
  - [x] Connected QShortcut.activatedAmbiguously to _on_shortcut_ambiguous logging warning event
  - [x] Implemented collect_live_shortcuts to discover all live window key sequence bindings
  - [x] Added automated TestHotkeyAmbiguousLogging and TestMainWindowShortcutUniqueness tests in tests/test_main_window_hotkeys.py
  - [x] Verified tests pass, lint passes, typecheck passes without new baseline errors; review passed
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1290/40-code-cleanup.md` created and accepted by review
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1290/50-observability.md` created and accepted by review
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1290/60-tech-debt.md` created and accepted by review
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/hotkeys.md` updated and accepted by review
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1290/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1290/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1290/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1290/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1290/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/hotkeys.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
