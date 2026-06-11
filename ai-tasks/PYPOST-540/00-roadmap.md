# Roadmap: PYPOST-540

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added optional `config_dir` parameter to `ConfigManager`.
  - [x] Added global `--config-dir` to `scripts/encryption_migrate.py`.
  - [x] Added CLI tests for config-dir override and missing-path exit.
- [x] **STEP 4: Code Cleanup**
  - [x] Scoped lint/format on changed files; cleanup report in `40-code-cleanup.md`.
- [x] **STEP 5: Observability**
  - [x] Extended CLI start log with `config_dir`; report in `50-observability.md`.
- [x] **STEP 6: Review and Technical Debt**
  - [x] Technical debt analysis in `60-tech-debt.md`.
- [x] **STEP 7: Dev Docs**
  - [x] Updated `doc/dev/encryption_key_migration.md` with `--config-dir`.
  - [x] Dev docs report in `70-dev-docs.md`.

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-540/10-requirements.md`
- Programming Language: Python 3.10+

### STEP 2: Architecture

- `ai-tasks/PYPOST-540/20-architecture.md`

### STEP 3: Development

- `pypost/core/config_manager.py`
- `scripts/encryption_migrate.py`
- `tests/test_encryption_migrate_cli.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-540/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-540/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-540/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/encryption_key_migration.md`
- `ai-tasks/PYPOST-540/70-dev-docs.md`

## Suggested Branch Name

`feature/PYPOST-540-encryption-migrate-config-dir`
