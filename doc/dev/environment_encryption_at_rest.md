# Environment Encryption at Rest

## Overview

PYPOST-447 introduces optional encryption-at-rest for sensitive environment variable values.
This feature protects hidden-key values in persisted environment storage.

Runtime request execution is unchanged: components still consume plain
`Environment.variables: Dict[str, str]` after load-time decryption.

## Configuration

Encryption is controlled by environment variables:

- `PYPOST_ENV_ENCRYPTION_ENABLED`
  - truthy values: `1`, `true`, `yes`, `on`
- `PYPOST_ENV_ENCRYPTION_KEY`
  - Fernet key used for encrypt/decrypt operations

If encryption is enabled and the key is missing, save/load error paths are triggered and
reported via logs and metrics.

## Data Flow

1. User edits environment values in UI.
2. `StorageManager.save_environments()` serializes environment payload.
3. Hidden-key values are encrypted with `EnvironmentSecretsCodec` when encryption is enabled.
4. Data is written atomically to `environments.json`.
5. On load, encrypted payloads are decrypted before creating `Environment` instances.

## Payload Format

Encrypted values are stored as envelope objects in `variables` map:

- `enc`: encryption marker (`true`)
- `v`: payload version (currently `1`)
- `alg`: algorithm (`fernet`)
- `kid`: key identifier (sha256 prefix of key material)
- `ct`: ciphertext token

Plain string values remain supported for backward compatibility.

## Modules

- `pypost/core/storage.py`
  - encryption/decryption orchestration in save/load path.
- `pypost/core/environment_secrets_codec.py`
  - envelope validation and crypto operations.
- `pypost/core/key_provider.py`
  - key resolution and key-id checks.
- `pypost/core/metrics.py`
  - encryption observability counters.

## Metrics

Prometheus counters:

- `environment_value_encryptions_total`
- `environment_value_decryptions_total`
- `environment_encryption_errors_total{stage,reason}`

`stage` values:

- `save`
- `load`

`reason` values currently emitted:

- `encrypt_failed`
- `decrypt_failed`
- `unsupported_format`

## Failure Behavior

- Missing key with encryption enabled:
  - save may fail with encryption error;
  - load returns no environments for failed payload set.
- Key-id mismatch:
  - decrypt failure path triggers error metric/log.
- Invalid envelope shape:
  - unsupported format error path triggers error metric/log.

## Tests

Primary coverage files:

- `tests/test_environment_secrets_codec.py`
- `tests/test_key_provider.py`
- `tests/test_storage_environments.py`
- `tests/test_env_persistence_e2e.py`

Project-wide regression:

```bash
make test
```
