# Roadmap: PYPOST-1145

## Task Metadata

- **Implementation language**: Python (PySide6 / Qt in `pypost/ui/dialogs/` and `pypost/ui/widgets/settings/`)
- **Branch name**: `refactor/PYPOST-1145-settings-tabbed-layout` *(reference only, do not switch)*

## Step Status

- [/] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1145/10-requirements.md`
- [/] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1145/20-architecture.md`
- [/] **STEP 3: Failing Repro Test**
  - `tests/test_settings_dialog_tabbed_layout.py` (red: no QTabWidget / wrong tab labels)
- [/] **STEP 4: Development**
  - [x] Refactored `SettingsDialog` to `QTabWidget` with five categorized pages
  - [x] Added `SETTINGS_TABS` widget id and `form_layout_index_of()` helper
  - [x] Updated layout-dependent tests in `test_settings_dialog.py`, `test_settings_encryption.py`, `test_settings_encryption_migration_ui.py`
  - [x] Green tests in `tests/test_settings_dialog_tabbed_layout.py`
- [/] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1145/40-code-cleanup.md`
- [/] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1145/50-observability.md`
- [/] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1145/60-tech-debt.md`
- [/] **STEP 8: Dev Docs**
  - `doc/dev/settings_dialog.md` — tabbed layout section
- [ ] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1145/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1145/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_settings_dialog_tabbed_layout.py`

### STEP 4: Development

- `pypost/ui/dialogs/settings_dialog.py`
- `pypost/ui/widget_ids.py`
- `tests/test_settings_dialog_tabbed_layout.py`
- `tests/test_settings_dialog.py`
- `tests/test_settings_encryption.py`
- `tests/test_settings_encryption_migration_ui.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1145/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1145/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1145/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/settings_dialog.md`

### COMMIT

- *(pending — commit prep only)*
