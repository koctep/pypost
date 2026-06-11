# PYPOST-543: Architecture

## Approach

Add `tests/test_encryption_migration_vault.py` mirroring
`tests/test_encryption_migration_key_sources.py` but configuring the secret-store spec with a
`vault` backend entry instead of `file`.

## Fixtures

| Fixture | Mechanism | Purpose |
| --- | --- | --- |
| `vault_spec` | Temp JSON spec + `PYPOST_ENV_ENCRYPTION_SECRETS_FILE` | Secret-store spec with vault backend |
| `mock_vault_http` | `patch` on `secret_store.requests.get` | Deterministic KV v2 registry payload |

## Scenarios

| ID | Stage | Operation | Setup |
| --- | --- | --- | --- |
| V1 | 4 | verify | Env-encrypted data; vault backend returns matching registry; env fallback |
| V2 | 4 | re-encrypt | Env-encrypted data; vault registry rotated to new active kid |

## Boundaries

- No production code changes.
- Helpers stay local to the test module.
- Reuse patterns from `test_encryption_migration_key_sources.py` and
  `test_key_sources_secret_store.py`.
