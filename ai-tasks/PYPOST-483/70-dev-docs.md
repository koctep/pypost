# PYPOST-483 — Developer Documentation

> Team Lead: team_lead
> Date: 2026-06-11
> Sprint: (current)

---

## 1. What Changed and Why

PYPOST-483 extends environment encryption-at-rest key resolution beyond a single environment
variable. The product now resolves Fernet key material from an ordered provider chain (environment,
OS keyring, secret store), supports configurable fallback in application settings, and enables
key rotation via per-source registries without breaking decrypt for historical `kid` values.

Runtime encrypt/decrypt boundaries are unchanged: `EnvironmentSecretsCodec` still depends only on
`KeyProvider`; settings persist policy (source strategy and fallback order) but never key material.

---

## 2. New and Updated Modules

- `pypost/core/key_sources/` (new package)
  - `EnvKeySource`, `KeyringKeySource`, `SecretStoreKeySource`, `KeySourceChain`
  - `FileSecretBackend`, `SecretBackendChain`, `KeyRegistry`, factories
- `pypost/core/encryption_key.py` (new)
  - Shared `EncryptionKey`, `build_key_id()`, `EnvironmentEncryptionError`
- `pypost/core/key_provider.py`
  - `ChainedKeyProvider`; thin backward-compatible `LocalKeyProvider`
- `pypost/core/encryption_config.py`
  - `resolve_key_source_chain()`, `build_key_provider(settings)` with chain wiring
  - `SUPPORTED_KEY_SOURCES`: `environment`, `keyring`, `secret_store`
- `pypost/models/settings.py`
  - `env_encryption_key_source_fallback: Optional[list[str]]`
- `pypost/ui/dialogs/settings_dialog.py`
  - Keyring and secret-store primary options; fallback order text field; per-source help
- `pypost/core/storage.py`
  - Uses `build_key_provider(settings)`; logs `source_chain`

---

## 3. Documentation Updated

- `doc/dev/environment_encryption_at_rest.md`
  - Updated architecture diagram and component table for provider chain
  - Added **Key source chain** (env, keyring, secret store roles)
  - Added **Fallback order configuration** (settings + resolution behavior)
  - Added **Key registry files** and **Key rotation workflow**
  - Expanded **Settings UI** fields and **API / Usage** (`resolve_key_source_chain`)
  - Expanded **Troubleshooting** (rotation, fallback, keyring, secret store, registry files)
  - Updated test file list (`test_key_sources_secret_store.py`)

---

## 4. Configuration Summary

| Source | Field / variable | Effect |
| --- | --- | --- |
| Settings | `env_encryption_key_source` | Primary: `environment`, `keyring`, `secret_store` |
| Settings | `env_encryption_key_source_fallback` | Optional ordered additional sources |
| Env var | `PYPOST_ENV_ENCRYPTION_KEY` | Active key for environment source |
| Env var | `PYPOST_ENV_ENCRYPTION_KEYS_FILE` | Env-channel rotation registry (optional) |
| Env var | `PYPOST_ENV_ENCRYPTION_SECRETS_FILE` | Secret-store spec for `secret_store` source |
| Keyring | service `pypost/env-encryption` | Entry `active` + entries named `{key_id}` |

When fallback is unset, only the primary source is attempted (env-only backward compatibility).

---

## 5. Testing

Focused suites:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_encryption_config.py \
  tests/test_key_provider.py \
  tests/test_key_sources_secret_store.py \
  tests/test_settings_encryption.py \
  tests/test_storage_environments.py
```

Full regression:

```bash
make test
```

---

## 6. Related Tickets

- `PYPOST-447` — encryption-at-rest foundation.
- `PYPOST-481` — user-facing encryption settings.
- `PYPOST-483` — multi-source key provider chain and rotation (this task).
- `PYPOST-487` — bulk re-encryption / migration when encryption settings change (follow-up).
