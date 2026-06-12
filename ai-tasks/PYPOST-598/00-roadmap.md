# Roadmap: PYPOST-598

## Programming Language

Python 3.10+ (PyPost project standard).

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Created `pypost/ui/widgets/settings/` package with eight domain section builders
  - [x] Refactored `settings_dialog.py` to thin coordinator facade; preserved public API and widget attrs
  - [x] All 69 targeted settings tests pass
- [x] **STEP 4: Code Cleanup**
  - [x] Lint clean on touched files; re-export noqa for public API
  - [x] `40-code-cleanup.md`
- [x] **STEP 5: Observability**
  - [x] Logging preserved under `pypost.ui.dialogs.settings_dialog`
  - [x] `50-observability.md`
- [x] **STEP 6: Review and Technical Debt**
  - [x] Verdict SAFE TO CLOSE; no new blockers
  - [x] `60-tech-debt.md`
- [x] **STEP 7: Dev Docs**
  - [x] Updated `doc/dev/settings_dialog.md`
  - [x] `70-dev-docs.md`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Parent Context

- Parent audit: [PYPOST-374](../PYPOST-374/30-dialogs-audit-report.md) finding **D1**
  (`SettingsDialog` multi-domain SRP violation).

## Suggested branch

`refactoring/PYPOST-598-split-settings-dialog`

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-598/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-598/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-598/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-598/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-598/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/settings_dialog.md`
- `ai-tasks/PYPOST-598/70-dev-docs.md`
