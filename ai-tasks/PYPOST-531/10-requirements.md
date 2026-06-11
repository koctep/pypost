# PYPOST-531: Integration tests for keyring/secret_store migration paths

## Goals

Operators rolling out Stage 2 (desktop keyring) and Stage 3 (team secret file) need confidence that
`EncryptionMigrationService` verify and bulk re-encrypt work when the primary key source is not
environment-only.

## Programming Language

Python 3.10+

## User Stories

- As a maintainer, I want integration tests that exercise verify with keyring and secret_store
  primaries so Stage 2–3 go/no-go checks are regression-protected.
- As a maintainer, I want re-encrypt covered under keyring and secret_store cutover scenarios so
  rotation rollouts do not rely on manual QA alone.

## Definition of Done

- Tests use mocked keyring and file-based secret_store fixtures (no OS keyring dependency).
- Verify and bulk re-encrypt succeed for Stage 2 (keyring primary + env fallback) and Stage 3
  (secret_store primary).
- Re-encrypt under a new active key is covered for both sources.
- Developer documentation lists the new test module.

## Out of Scope

- Vault backend integration tests (Stage 4).
- CLI end-to-end tests (covered separately).
- Changes to migration service or key source implementations.

## Acceptance Criteria

1. Keyring-primary verify decrypts envelopes encrypted under env when fallback chain resolves keys.
2. Keyring-primary bulk re-encrypt moves envelopes to the keyring active `kid`.
3. Secret-store-primary verify and re-encrypt behave equivalently via spec file fixtures.
4. Tests pass in CI without the `keyring` package installed (mocked module).
