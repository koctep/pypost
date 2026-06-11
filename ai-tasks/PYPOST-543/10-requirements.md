# PYPOST-543: Vault backend migration integration test

## Goals

Operators rolling out Stage 4 (central secrets via HashiCorp Vault) need confidence that
`EncryptionMigrationService` verify and bulk re-encrypt work when the secret-store spec resolves
keys through a Vault KV backend rather than a local file.

## Programming Language

Python 3.10+

## User Stories

- As a maintainer, I want integration tests that exercise verify with a Vault-backed
  secret_store primary so Stage 4 go/no-go checks are regression-protected.
- As a maintainer, I want re-encrypt covered under a Vault registry cutover scenario so
  centrally managed key rotation does not rely on manual QA alone.

## Definition of Done

- Tests use a mocked Vault HTTP endpoint (no live Vault dependency).
- Verify and bulk re-encrypt succeed for Stage 4 (secret_store primary with vault backend).
- Re-encrypt under a new active key is covered.
- Developer documentation lists the new test module.

## Out of Scope

- Live Vault or network integration in CI.
- Changes to migration service or Vault backend implementations.
- CLI end-to-end tests (covered separately).

## Acceptance Criteria

1. Vault-backend verify decrypts envelopes encrypted under env when the registry resolves via
   mocked KV response.
2. Vault-backend bulk re-encrypt moves envelopes to the Vault registry active `kid`.
3. Tests pass in CI without a running Vault server.
4. `doc/dev/encryption_key_migration.md` documents the new test module.
