# PYPOST-1225: [Libraries] At-Rest Encryption for Local Overlay Secrets

## Research

`LocalOverlayManager` (`pypost/core/local_overlay_manager.py`) manages local overlay storage under `~/.pypost/libraries_data/<library-id>/overlay.json`.
The application's core encryption layer (`pypost/core/environment_secrets_codec.py`) provides:
- `EnvironmentSecretsCodec.encrypt(value: str) -> EncryptedValueEnvelope`
- `EnvironmentSecretsCodec.decrypt(payload: dict[str, Any]) -> str`
- Envelope models `EncryptedValueEnvelope` and `EncryptedValueEnvelopeV2` with `to_json()` serialization.

Integrating `EnvironmentSecretsCodec` into `LocalOverlayManager`:
- Provides optional symmetric encryption for sensitive entries in `overlay.secrets` on disk.
- Preserves plaintext transparency for in-memory `LocalLibraryOverlay` instances.
- Maintains backward compatibility: plaintext secret strings in existing files are read directly without error.

## Implementation Plan

1. **Step 3 (Failing Repro):**
   - Write automated tests in `tests/test_library_overlay_encryption.py` (or `tests/test_library_manifest_and_overlay_repro.py`):
     - Test saving an overlay with secrets using `LocalOverlayManager(secrets_codec=codec)`; assert `overlay.json` on disk contains encrypted envelope structures in `secrets` (`{"enc": True, ...}`).
     - Test loading the encrypted `overlay.json` with `LocalOverlayManager(secrets_codec=codec)`; assert `get_overlay` returns decrypted plaintext secrets.
     - Test loading legacy unencrypted plaintext `overlay.json` with `LocalOverlayManager(secrets_codec=codec)`; assert plaintext secrets are returned without error.
   - Confirm tests fail on unmodified code.

2. **Step 4 (Development):**
   - Update `LocalOverlayManager.__init__` to accept `secrets_codec: Optional[EnvironmentSecretsCodec] = None`.
   - Update `save_overlay` to encrypt string secrets in `overlay.secrets` when `secrets_codec` is set.
   - Update `get_overlay` to decrypt encrypted envelopes in `data["secrets"]` when `secrets_codec` is set.
   - Run tests and verify all pass.

3. **Steps 5–8:**
   - Code cleanup, observability logging, tech debt analysis, and dev docs.

## Architecture

```
+-------------------------------------------------------------+
|                  LocalOverlayManager                        |
+-------------------------------------------------------------+
|  __init__(base_dir, secrets_codec=None)                     |
|                                                             |
|  save_overlay(overlay: LocalLibraryOverlay)                 |
|    - secrets_codec present?                                 |
|        -> encrypt secrets -> {"enc": True, "v": 1, ...}     |
|        -> atomic write to overlay.json (0o600)              |
|                                                             |
|  get_overlay(library_id) -> LocalLibraryOverlay             |
|    - read overlay.json                                      |
|    - is secret envelope dict?                               |
|        -> secrets_codec.decrypt(env) -> plaintext string    |
|        -> return LocalLibraryOverlay with plaintext secrets |
|    - is plain string?                                       |
|        -> keep string (backward compat)                     |
+-------------------------------------------------------------+
```

### Module Responsibilities & Interfaces

- `LocalOverlayManager`:
  - `secrets_codec: Optional[EnvironmentSecretsCodec]`: Optional encryption codec.
  - `save_overlay(overlay: LocalLibraryOverlay) -> Path`: Persists overlay with encrypted secret envelopes when codec configured.
  - `get_overlay(library_id: str) -> LocalLibraryOverlay`: Deserializes overlay, transparently decrypting secret envelopes.

## Q&A

| Question | Answer |
| --- | --- |
| What happens if a secret is already encrypted? | If already an encrypted envelope dictionary, it is preserved without double-encrypting. |
| Are non-secret overrides encrypted? | No. Only `overlay.secrets` values are encrypted. |
