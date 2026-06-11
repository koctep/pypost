# PYPOST-532: Dev Docs

## Updated

No `doc/dev/` changes required. `doc/dev/encryption_key_migration.md` already documents
`encrypt-plaintext --dry-run` operator usage (PYPOST-487).

## Cross-links

- Parent runbook: `doc/dev/encryption_key_migration.md`
- Service dry-run test: `tests/test_encryption_migration.py::test_encrypt_plaintext_hidden_dry_run_projects_active_kid`
- CLI parity test: `tests/test_encryption_migrate_cli.py::test_cli_encrypt_plaintext_dry_run`
