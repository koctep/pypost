# PYPOST-531: Architecture

## Approach

Add a dedicated test module `tests/test_encryption_migration_key_sources.py` that reuses the
`StorageManager` + `EncryptionMigrationService` stack from existing migration tests but configures
`AppSettings` for Stage 2–3 primary sources.

## Fixtures

| Fixture | Mechanism | Purpose |
| --- | --- | --- |
| `mock_keyring` | `unittest.mock.patch.dict(sys.modules, {"keyring": mock})` | Deterministic keyring entries under `pypost/env-encryption` |
| `secret_store_spec` | Temp JSON spec + `PYPOST_ENV_ENCRYPTION_SECRETS_FILE` | File-backend registry without Vault |

## Scenarios

| ID | Stage | Operation | Setup |
| --- | --- | --- | --- |
| K1 | 2 | verify | Env-encrypted data; keyring primary with same key; env fallback |
| K2 | 2 | re-encrypt | Env-encrypted data; keyring active new key; historical kid in keyring |
| S1 | 3 | verify | Env-encrypted data; secret_store primary with matching registry |
| S2 | 3 | re-encrypt | Env-encrypted data; secret_store registry rotated to new active kid |

## Boundaries

- No production code changes.
- Helpers stay local to the test module (no new public API).
- Follow patterns from `test_key_provider.py` and `test_encryption_migration.py`.
