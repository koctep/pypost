# PYPOST-530: Code Cleanup

## Lint and format

- No new linter issues in `scripts/encryption_migrate.py`, `pypost/core/storage.py`, or CLI tests.
- Imports grouped per project style (`json` added with stdlib).

## Scope check

- `StorageManager.data_dir` override is optional with default unchanged for existing callers.
- JSON helpers are CLI-local; no duplicate serialization in `encryption_migration.py`.

## Review

Ready for observability and tech-debt review.
