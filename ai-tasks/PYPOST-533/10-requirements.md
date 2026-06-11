# PYPOST-533: Envelope v2 schema and version dispatch

## Goals

Prepare encrypted environment value envelopes for future algorithm and metadata changes without
breaking existing v1 on-disk payloads in `environments.json`.

## Programming Language

Python 3.10+

## User Stories

- As a maintainer adding a new encryption algorithm, I want an explicit v2 envelope schema so
  fields like nonce and auth tag are first-class rather than ad hoc extensions to v1.
- As an operator with existing encrypted data, I want v1 envelopes to keep parsing and decrypting
  unchanged after this change.
- As a developer integrating decrypt paths, I want `from_payload()` to route by version so v2
  validation stays isolated from v1 rules.

## Definition of Done

- v2 envelope schema is documented (fields, algorithm-specific requirements, optional metadata).
- `EncryptedValueEnvelope.from_payload()` dispatches on `v` and returns a typed v1 or v2 model.
- v1 acceptance and rejection behavior is unchanged (same error messages).
- v2 payloads can be parsed and validated; encrypt still emits v1; decrypt rejects unsupported v2
  with a clear operator-facing error.
- Unit tests cover dispatch, v2 validation, and v1 regression cases.
- Developer documentation updated.

## Out of Scope

- Implementing AES-GCM (or other v2 algorithm) encrypt/decrypt in `EnvironmentSecretsCodec`.
- Migrating on-disk v1 records to v2.
- Changing adapter or storage layers beyond codec dispatch.

## Acceptance Criteria

1. Valid v1 payloads parse into `EncryptedValueEnvelope` with the same field normalization as
   before.
2. Invalid v1 payloads raise `EnvironmentEncryptionError` with unchanged messages.
3. Valid v2 payloads parse into `EncryptedValueEnvelopeV2`; `aes-gcm` requires `iv` and `tag`.
4. Unknown `v` values raise `Unsupported encrypted payload version`.
5. `EnvironmentSecretsCodec.encrypt()` continues to produce v1 envelopes only.
6. `EnvironmentSecretsCodec.decrypt()` succeeds for v1 and rejects v2 with a clear error.
