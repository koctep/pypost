# Roadmap: PYPOST-484

**Programming language:** Python 3.10+

**Suggested branch:** `refactoring/PYPOST-484-typed-envelope-payload`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `EncryptedValueEnvelope.from_payload()` with centralized v1 validation
  - [x] Replaced manual `_validate_payload` in `EnvironmentSecretsCodec.decrypt`
  - [x] Added unit tests for typed payload parsing
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

- `ai-tasks/PYPOST-484/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-484/20-architecture.md`

### STEP 3: Development

- `pypost/core/environment_secrets_codec.py`
- `tests/test_environment_secrets_codec.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-484/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-484/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-484/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/environment_encryption_at_rest.md`
- `ai-tasks/PYPOST-484/70-dev-docs.md`
