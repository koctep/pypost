# PYPOST-483: Technical Debt Analysis

## Shortcuts Taken

- **Secret-store v1 is file-backend only.** `SecretBackendChain` supports only `type: file`;
  vault HTTP, env-indirection, and other backends from the architecture are deferred.
- **Fallback order UI is a free-text comma field** (`QLineEdit`) rather than an ordered
  multi-select. Invalid tokens are silently dropped by `parse_key_source_fallback()` with no
  user feedback.
- **Registry/spec files are re-read on every key lookup** — no in-process caching or mtime-based
  invalidation. Acceptable for desktop save/load paths but adds disk I/O on each encrypt/decrypt.
- **`SecretBackendChain.resolve_registry()` falls back to inline spec keys** when all configured
  backends fail. This preserves operator convenience but can mask a misconfigured backend path.
- **`keyring` is listed in `requirements.txt`** while `KeyringKeySource` still guards the import
  and treats a missing package as unavailable. Dependency posture is intentionally mixed.
- **Broad `except Exception` in `KeyringKeySource`** swallows OS-backend errors as “unavailable”
  rather than surfacing distinct failure reasons to the operator.

## Code Quality Issues

- **`SUPPORTED_KEY_SOURCES` is duplicated** in `encryption_config.py` and `settings_dialog.py`;
  drift risk when adding future sources.
- **Backend factory logic is duplicated** — `create_secret_backend()` in `factory.py` and
  `_create_backend_for_type()` in `secret_store.py` implement the same type dispatch.
- **`SecretBackendChain.__init__` accepts an unused backends list**; backends are instantiated
  per-resolve inside `resolve_registry()`. Confusing API surface for maintainers.
- **`env_encryption_key_source` remains `Optional[str]`** in `AppSettings` instead of the
  `EncryptionKeySource` literal used in `encryption_config.py`.
- **`SettingsDialog.accept()` manually lists every `AppSettings` field** when saving (inherited
  from PYPOST-481). New encryption fields added another touch point to this method.
- **No Fernet key-material validation** before constructing `EncryptionKey`; invalid registry
  entries fail later at encrypt/decrypt with less actionable errors.
- **Unused `EnvKeySource._key_from_material()`** — dead helper left after registry-path refactor.
- **`doc/dev/environment_encryption_at_rest.md` still describes the pre-483 architecture**
  (`LocalKeyProvider`-only factory diagram). Update deferred to STEP 7.

## Missing Tests

- **No `parse_key_source_fallback()` unit tests** — invalid/empty/duplicate token handling is
  untested; silent drops are undocumented in tests.
- **No chain `resolve_by_id` fallback test** — `test_key_source_chain_fallback` covers active
  key only; by-id cross-source fallback is unverified.
- **No `SecretStoreKeySource.try_resolve_by_id()` test** for historical keys (inline spec or
  backend-loaded registry).
- **No test for `SecretBackendChain` inline-spec fallback** when all file backends are missing or
  invalid.
- **Limited `EnvKeySource` edge cases** — invalid/malformed `PYPOST_ENV_ENCRYPTION_KEYS_FILE`,
  empty registry, and precedence when both `KEYS_FILE` and `ENV_KEY` are set.
- **No storage integration test** applying a multi-source chain (`keyring` → `environment`) via
  `StorageManager.apply_encryption_settings()` with real encrypt/decrypt round-trip.
- **No end-to-end UI test** for `MainWindow.open_settings()` applying key-source/fallback changes
  to `StorageManager` (carried forward from PYPOST-481 scope).
- **No UI test for `secret_store` help text** (keyring help is covered).

## Performance Concerns

- **Per-call disk reads** for env keys file, secret-store spec, and file backends on every
  `get_current_key()` / `get_key_by_id()` invocation.
- **Per-call keyring OS lookups** on the encrypt/decrypt hot path when keyring is in the chain.
- **INFO-level chain attempt logs** on every resolution call may be noisy in high-churn sessions;
  acceptable for operability today but worth revisiting if log volume becomes an issue.

## Follow-up Tasks

- Add operator/dev documentation for key sources, fallback order, and rotation workflow in
  `doc/dev/environment_encryption_at_rest.md` — completed in STEP 7.
- Implement bulk re-encryption / migration tooling when encryption settings change.
- Implement bulk re-encryption / migration tooling when encryption settings change. — [PYPOST-487](https://pypost.atlassian.net/browse/PYPOST-487)
- Add vault and env-indirection secret-store backends beyond file v1.
- Add vault and env-indirection secret-store backends beyond file v1. — [PYPOST-500](https://pypost.atlassian.net/browse/PYPOST-500)
- Add end-to-end test: Settings dialog → `StorageManager.apply_encryption_settings()` →
  encrypt/decrypt with multi-source chain.
- encrypt/decrypt with multi-source chain. — [PYPOST-501](https://pypost.atlassian.net/browse/PYPOST-501)
- Add unit tests for `parse_key_source_fallback()`, chain by-id fallback, and secret-store
  historical key resolution.
- historical key resolution. — [PYPOST-502](https://pypost.atlassian.net/browse/PYPOST-502)
- Consolidate `SUPPORTED_KEY_SOURCES` and secret-backend factory into a single module.
- Consolidate `SUPPORTED_KEY_SOURCES` and secret-backend factory into a single module. — [PYPOST-503](https://pypost.atlassian.net/browse/PYPOST-503)
- Consider registry caching with file-mtime invalidation for env/secret-store sources.
- Consider registry caching with file-mtime invalidation for env/secret-store sources. — [PYPOST-504](https://pypost.atlassian.net/browse/PYPOST-504)
- Warn in Settings UI when fallback text contains unsupported or duplicate entries.
- Warn in Settings UI when fallback text contains unsupported or duplicate entries. — [PYPOST-505](https://pypost.atlassian.net/browse/PYPOST-505)
- Validate Fernet key material at registry load time with clear, safe error messages.
- Validate Fernet key material at registry load time with clear, safe error messages. — [PYPOST-506](https://pypost.atlassian.net/browse/PYPOST-506)
- Evaluate extracting environment serialization/encryption from `StorageManager`.
- Evaluate extracting environment serialization/encryption from `StorageManager`. — [PYPOST-482](https://pypost.atlassian.net/browse/PYPOST-482)
- Clarify `keyring` packaging: optional extra vs required dependency, documented in install
  guidance.
- guidance. — [PYPOST-507](https://pypost.atlassian.net/browse/PYPOST-507)
