# Roadmap: PYPOST-599

## Programming Language

Python 3.10+ (PyPost project standard).

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `pypost/ui/hotkeys.py` registry helpers (`register_hotkey`, `tag_action`, `collect_hotkey_rows`)
  - [x] Refactored `MainWindow._setup_shortcuts` and `RequestEditor._setup_shortcuts` to tag QActions
  - [x] `HotkeysDialog` derives rows from parent widget QAction metadata
  - [x] Added `tests/test_hotkeys.py` (5 tests)
- [x] **STEP 4: Code Cleanup**
  - [x] Lint clean on touched files (pre-existing E501 in `request_editor.py` line 63 unchanged)
  - [x] `40-code-cleanup.md`
- [x] **STEP 5: Observability**
  - [x] No new logging required (display-only dialog)
  - [x] `50-observability.md`
- [x] **STEP 6: Review and Technical Debt**
  - [x] Verdict SAFE TO CLOSE; no blockers
  - [x] `60-tech-debt.md`
- [x] **STEP 7: Dev Docs**
  - [x] Updated `doc/dev/hotkeys.md`, `doc/dev/solid_audit.md`, `doc/dev/tech-debt/PYPOST-11.md`
  - [x] `70-dev-docs.md`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Parent Context

- Parent audit: [PYPOST-374](../PYPOST-374/30-dialogs-audit-report.md) finding **D2**
  (`HotkeysDialog` hardcoded shortcuts vs app actions).

## Suggested branch

`refactoring/PYPOST-599-hotkeys-from-actions`

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-599/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-599/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-599/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-599/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-599/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/hotkeys.md`
- `ai-tasks/PYPOST-599/70-dev-docs.md`
