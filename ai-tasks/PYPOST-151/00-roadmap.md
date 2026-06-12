# Roadmap: PYPOST-151

**Programming language:** Python (PySide6)

**Suggested branch:** `fix/PYPOST-151-settings-bind-address-validation`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `bind_address_validation` module with host/port validators
  - [x] Wired validation into `SettingsDialog.accept()` for MCP and metrics fields
  - [x] Added unit and Qt-level tests
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-151/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-151/20-architecture.md`

### STEP 3: Development

- `pypost/core/bind_address_validation.py`
- `pypost/ui/dialogs/settings_dialog.py`
- `pypost/ui/collection_item_dialogs.py`
- `tests/test_bind_address_validation.py`
- `tests/test_settings_dialog.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-151/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-151/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-151/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/settings_dialog.md`
