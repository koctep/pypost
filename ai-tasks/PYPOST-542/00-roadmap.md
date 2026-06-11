# Roadmap: PYPOST-542

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `EnvironmentSecretsCodec.encrypt_v2()` (fernet + aes-gcm).
  - [x] Extended adapter/storage save path with `target_envelope_version=2`.
  - [x] Added `v1_envelope_count` / `v2_envelope_count` to inventory.
  - [x] Added `EncryptionMigrationService.upgrade_envelopes_to_v2()`.
  - [x] Added CLI `upgrade-v2` subcommand and tests.
- [x] **STEP 4: Code Cleanup**
  - [x] Scoped lint on changed files; report in `40-code-cleanup.md`.
- [x] **STEP 5: Observability**
  - [x] Extended inventory and operation logs for v1/v2 counts; report in `50-observability.md`.
- [x] **STEP 6: Review and Technical Debt**
  - [x] Technical debt analysis in `60-tech-debt.md`.
- [x] **STEP 7: Dev Docs**
  - [x] Updated `doc/dev/encryption_key_migration.md` and `environment_encryption_at_rest.md`.
  - [x] Dev docs report in `70-dev-docs.md`.

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-542/10-requirements.md`
- Programming Language: Python 3.10+

### STEP 2: Architecture

- `ai-tasks/PYPOST-542/20-architecture.md`

### STEP 3: Development

- `pypost/core/environment_secrets_codec.py`
- `pypost/core/environment_variables_adapter.py`
- `pypost/core/storage.py`
- `pypost/core/encryption_migration.py`
- `scripts/encryption_migrate.py`
- `tests/test_environment_secrets_codec.py`
- `tests/test_encryption_migration.py`
- `tests/test_encryption_migrate_cli.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-542/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-542/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-542/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/encryption_key_migration.md`
- `doc/dev/environment_encryption_at_rest.md`
- `ai-tasks/PYPOST-542/70-dev-docs.md`

## Suggested Branch Name

`feature/PYPOST-542-v1-v2-envelope-upgrade`
