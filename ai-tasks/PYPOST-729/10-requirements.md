# PYPOST-729: Fix flake8 violations for make lint

## Goals

Unblock `make lint` in CI and local development by eliminating the four flake8
violations that currently cause a non-zero exit code.

## User Stories

- As a developer, I want `make lint` to pass so I can integrate linting into the
  CI pipeline without false failures.

## Definition of Done

- `make lint` exits with code 0.
- No new flake8 violations introduced.
- All existing tests continue to pass.

## Task Description

Four flake8 violations currently block `make lint`:

| File | Line | Code | Description |
|------|------|------|-------------|
| `pypost/core/encryption_migration.py` | 104 | F841 | `error_prefix` assigned but never used |
| `pypost/core/encryption_migration_worker.py` | 10 | F401 | `MigrationReport` imported but unused |
| `pypost/ui/widgets/mixins.py` | 374 | W391 | blank line at end of file |
| `pypost/ui/widgets/request_editor.py` | 65 | E501 | line too long (104 > 100 chars) |

## Q&A

**Q: Should `error_prefix` be used somewhere in the function?**
A: No. The errors block at lines 127–130 uses a hardcoded `"Errors:"` string.
   The variable is a dead assignment and can be removed safely.

**Q: Is `MigrationReport` used elsewhere in the worker module?**
A: No. `grep` confirms only one occurrence (the import line). Safe to remove.
