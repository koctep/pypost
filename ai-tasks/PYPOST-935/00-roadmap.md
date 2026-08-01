# Roadmap: PYPOST-935

**Programming language:** Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] Red: `tests/test_settings_dialog.py` —
    `TestSettingsDialogWidgetIdentity` — `ImportError: cannot import name
    'SETTINGS_DIALOG' from 'pypost.ui.widget_ids'`
- [x] **STEP 4: Development**
  - [x] Added `SETTINGS_DIALOG` constant in `pypost/ui/widget_ids.py`
  - [x] Applied `set_widget_id(self, SETTINGS_DIALOG)` in `SettingsDialog.__init__`
  - [x] Migrated dialog-settle predicate to `objectName == SETTINGS_DIALOG`
  - [x] Added `dialog_object_name` to `_modal_diag()` diagnostics
  - [x] Documented `SETTINGS_DIALOG` in `doc/dev/ui_identity.md` and
    `doc/dev/agent_dialog_settle.md`
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-935/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-935/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-935/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-935/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-935/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`
