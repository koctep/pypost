# PYPOST-1018: [PYPOST-542] Default Runtime Encrypt to v2

## Research

In `pypost/core/environment_secrets_codec.py`, `EnvironmentSecretsCodec` previously defaulted to version 1 envelopes (`EncryptedValueEnvelope.VERSION = 1`) for `encrypt()`, while offering `encrypt_v2()` separately.
In `pypost/core/environment_variables_adapter.py`, `serialize_environment()` defaulted to version 1 envelopes when `target_envelope_version` was not explicitly passed.

Now that the v2 envelope specification is supported and stable across storage and migration layers, the default runtime path should be flipped to v2.

## Implementation Plan

1. **Step 3 (Failing Repro):**
   - Create `tests/test_default_runtime_encrypt_v2.py`:
     - Verify `codec.encrypt("secret")` returns `EncryptedValueEnvelopeV2` with `v == 2`.
     - Verify `adapter.serialize_environment(env)` serializes hidden keys as `v == 2` envelopes by default.
     - Verify `EnvironmentSecretsCodec.VERSION == 2`.
     - Verify `codec.encrypt_v1("secret")` explicitly creates a `v == 1` envelope.
     - Verify transparent decryption of both v1 and v2 envelopes.
   - Confirm tests fail on unmodified code.

2. **Step 4 (Development):**
   - In `pypost/core/environment_secrets_codec.py`:
     - Set `EnvironmentSecretsCodec.VERSION = EncryptedValueEnvelopeV2.VERSION`.
     - Implement `encrypt_v1()` for explicit version 1 creation.
     - Update `encrypt()` to produce `EncryptedValueEnvelopeV2` (delegating to `encrypt_v2`).
   - In `pypost/core/environment_variables_adapter.py`:
     - Update `serialize_environment` so `target_envelope_version` defaults to `2`.
     - Support `target_envelope_version=1` via `encrypt_v1()`.
   - Update existing unit tests if any strictly assert `v == 1` from `codec.encrypt()`.
   - Verify tests pass cleanly.

3. **Steps 5–8:**
   - Code cleanup, observability logging, tech debt analysis, and dev docs.

## Architecture

```
+--------------------------------------------------------------------------+
|                       EnvironmentSecretsCodec                            |
+--------------------------------------------------------------------------+
|                                                                          |
|  - VERSION = 2 (EncryptedValueEnvelopeV2.VERSION)                        |
|                                                                          |
|  - encrypt(value) -> EncryptedValueEnvelopeV2 (Default: v2)              |
|  - encrypt_v2(value, algorithm=...) -> EncryptedValueEnvelopeV2          |
|  - encrypt_v1(value) -> EncryptedValueEnvelope (Legacy explicit)         |
|                                                                          |
|  - decrypt(payload) -> Dispatches to v1 or v2 based on payload["v"]      |
|                                                                          |
+--------------------------------------------------------------------------+
```

## Q&A

| Question | Answer |
| --- | --- |
| What happens to files saved before this change? | They contain v1 envelopes and will continue to be decrypted transparently by `codec.decrypt()`. |
| When will existing v1 envelopes be upgraded to v2? | Either upon saving modifications to an environment in the UI, or via the `upgrade-v2` CLI migration command. |
