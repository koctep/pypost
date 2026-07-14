# PYPOST-737: Dev Docs

## Changes

Updated `doc/dev/maintainability_audit.md`:

- Lint section reflects `make lint` **PASS** (flake8 clean).
- R-P3-001 dead-code items (`error_prefix`, `MigrationReport` import) marked **Done**
  (PYPOST-729 / PYPOST-737).
- Worker module path corrected to `pypost/core/qt/encryption_migration_worker.py`.

## Related docs

- `doc/dev/setup.md` — `make lint` usage (unchanged).
