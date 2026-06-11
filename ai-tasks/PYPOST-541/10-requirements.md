# PYPOST-541: Implement v2 envelope decrypt handlers

## Goals

Enable decryption of v2 encrypted environment value envelopes so encryption migration and
on-disk adoption of v2 payloads can proceed without breaking existing v1 data.

## Programming Language

Python 3.10+

## User Stories

- As an operator migrating encrypted environments, I want v2 envelopes on disk to decrypt with
  the same key material as v1 so rotation and re-encryption workflows keep working.
- As a maintainer, I want algorithm-specific v2 decrypt paths (fernet and aes-gcm) isolated from
  v1 logic so future algorithms can extend the v2 model safely.
- As a developer, I want v1 decrypt behavior unchanged so existing deployments are unaffected.

## Definition of Done

- `EnvironmentSecretsCodec.decrypt()` decrypts valid v2 `fernet` envelopes using `kid` + `ct`.
- `EnvironmentSecretsCodec.decrypt()` decrypts valid v2 `aes-gcm` envelopes using `kid`, `iv`,
  `ct`, and `tag`.
- Invalid v2 ciphertext raises the same operator-facing error as v1 decrypt failures.
- v1 parse/decrypt behavior and error messages are unchanged.
- Unit tests cover v2 fernet and aes-gcm success and aes-gcm auth failure.
- Developer documentation reflects v2 decrypt support.

## Out of Scope

- v2 `encrypt()` or bulk v1→v2 migration tooling.
- New key source types or envelope schema changes.

## Acceptance Criteria

1. v2 fernet payload decrypts to the original plaintext with the matching registered key.
2. v2 aes-gcm payload decrypts when `iv`, `ct`, and `tag` are valid base64 and auth succeeds.
3. v2 aes-gcm decrypt with invalid tag raises `EnvironmentEncryptionError` with the standard
   decrypt failure message.
4. All existing v1 codec tests continue to pass.
