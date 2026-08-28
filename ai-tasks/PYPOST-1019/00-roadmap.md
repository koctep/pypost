# Roadmap: PYPOST-1019

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_settings_encryption_migration_ui.py`
- [x] **STEP 4: Development**
  - [x] Added `upgrade_v2` operation support in `EncryptionMigrationWorker`, added `confirm_upgrade_envelopes_v2` dialog, wired "Upgrade encrypted values to v2" button in `EncryptionMigrationSection` and `SettingsDialog`.
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Technical Debt Analysis**
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/encryption_key_migration.md`
- [ ] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1019/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1019/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1019/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1019/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1019/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
