# Roadmap: PYPOST-530

Suggested branch: `feature/PYPOST-530-cli-json-data-dir`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] `--json` structured stdout for all subcommands
  - [x] `--data-dir` override for backup-restore workflows
  - [x] CLI tests for JSON and data-dir paths
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

- `ai-tasks/PYPOST-530/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-530/20-architecture.md`

### STEP 3: Development

- `scripts/encryption_migrate.py`
- `pypost/core/storage.py`
- `tests/test_encryption_migrate_cli.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-530/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-530/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-530/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/encryption_key_migration.md`
- `ai-tasks/PYPOST-530/70-dev-docs.md`
