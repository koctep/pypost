# PYPOST-541: Code Cleanup

## Actions

- Renamed `_ensure_fernet_available` → `_ensure_crypto_available` (AES-GCM requires same dep).
- Grouped v2 decrypt helpers under `_decrypt_v2` / `_decrypt_aes_gcm`.
- No unused imports; flake8 clean on touched modules.

## Files reviewed

- `pypost/core/environment_secrets_codec.py`
- `tests/test_environment_secrets_codec.py`
