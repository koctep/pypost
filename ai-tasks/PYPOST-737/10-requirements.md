# PYPOST-737: Remove dead code flagged by flake8

## Goals

Close PYPOST-687 audit finding **R-P3-001 (DC-001, DC-002)** by ensuring flake8 F841/F401
violations in encryption migration modules are eliminated, keeping `make lint` clean.

## User Stories

- As a developer, I want no unused variables or imports in encryption migration code so
  static analysis stays trustworthy and CI lint gates can pass.

## Definition of Done

- No F841 `error_prefix` assignment in `pypost/core/encryption_migration.py`.
- No F401 unused `MigrationReport` import in the encryption migration worker module.
- `make lint` and `make check` exit 0.

## Task Description

Parent audit PYPOST-687 flagged two dead-code items (R-P3-001):

| File | Code | Description |
| --- | --- | --- |
| `pypost/core/encryption_migration.py` | F841 | `error_prefix` assigned but never used |
| `pypost/core/encryption_migration_worker.py` | F401 | `MigrationReport` imported but unused |

The worker module now lives at `pypost/core/qt/encryption_migration_worker.py` (PYPOST-642).

## Q&A

**Q: Were these already fixed in PYPOST-729?**
A: Yes. PYPOST-729 removed both violations along with two other flake8 issues. This ticket
verifies the remediations and updates audit documentation.

**Q: Should `error_prefix` be wired into error formatting?**
A: No. The errors block uses a hardcoded `"Errors:"` label; the variable was dead code.
