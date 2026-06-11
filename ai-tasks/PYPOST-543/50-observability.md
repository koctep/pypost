# PYPOST-543: Observability

## Scope

Test-only task — no new production logging or metrics.

## Existing Coverage

Migration service logs (`encryption_migration_verify_*`, `encryption_migration_operation_*`) fire
unchanged when tests invoke `EncryptionMigrationService`. Vault backend debug logs
(`vault_backend_fetch_failed`, `vault_backend_token_missing`) remain covered by
`tests/test_key_sources_secret_store.py`.

## Verification

- [x] No duplicate or missing log assertions required for integration tests
- [x] Test failures surface via pytest assertions on `MigrationReport.success`
