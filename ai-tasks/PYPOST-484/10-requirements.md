# PYPOST-484: Replace manual envelope validation with typed payload model

## Goals

Environment encryption at rest (PYPOST-447) stores hidden values as JSON envelope objects.
Validation of those envelopes is currently scattered as manual dict checks in the codec. As the
schema evolves, ad-hoc validation is error-prone and duplicates rules between encrypt and decrypt
paths. This task centralizes envelope rules in a typed model while preserving existing v1 on-disk
payloads.

## User Stories

- As a maintainer, I want envelope schema rules defined in one place so adding fields or versions
  does not require hunting through imperative validation code.
- As a developer, I want decrypt failures to keep the same error semantics so existing tests and
  operator troubleshooting remain valid.
- As an operator, I want existing `environments.json` files with v1 envelopes to load without
  migration.

## Definition of Done

- Encrypted envelope parsing and validation use a typed payload model (`EncryptedValueEnvelope`).
- Version and algorithm checks are centralized on the model.
- `EnvironmentSecretsCodec.decrypt` uses the model instead of manual `_validate_payload`.
- Existing v1 envelope JSON continues to encrypt/decrypt with unchanged on-disk format.
- Unit tests cover invalid payloads and valid v1 round-trip via `from_payload`.
- Developer documentation describes the typed envelope model.

## Task Description

PYPOST-447 technical debt identified manual envelope validation in
`environment_secrets_codec.py` as a maintainability risk. This task introduces a typed payload
model that owns v1 schema validation and is used on the decrypt path.

### In Scope

- Extend `EncryptedValueEnvelope` with `from_payload` validation factory.
- Remove duplicate manual validation from `EnvironmentSecretsCodec`.
- Preserve error messages and v1 field requirements (`enc`, `v`, `alg`, `kid`, `ct`).
- Add focused unit tests.

### Out of Scope

- New envelope versions or algorithms.
- Changes to encryption policy, key provider chain, or storage adapter.
- Bulk migration or re-encryption tooling (PYPOST-487).

## Functional Requirements

- Valid v1 payloads must parse into `EncryptedValueEnvelope` with normalized `kid` and `ct` strings.
- Invalid markers, versions, algorithms, or missing fields must raise `EnvironmentEncryptionError`
  with the same messages as before.
- `encrypt` output must remain compatible with `from_payload` parsing.

## Non-functional Requirements

- **Backward compatibility:** no changes to persisted envelope JSON shape.
- **Maintainability:** single source of truth for v1 schema constants and validation.
- **Testability:** `from_payload` testable without Fernet or key provider mocks.

## Constraints and Assumptions

- Python 3.10+; project line-length and style rules apply.
- Fernet remains the only supported algorithm in v1.
- Plain string environment values remain outside the envelope model.

## Main Entities and Interactions

- **Encrypted value envelope:** typed representation of a persisted encrypted variable value.
- **Secrets codec:** encrypts plaintext to envelopes and decrypts envelopes via the typed model.
- **Environment variables adapter:** detects dict envelopes and delegates decrypt to the codec.

## Q&A

- **Why not introduce v2 now?** Version checks stay centralized so future versions can add
  sibling parsers without changing decrypt call sites.
- **Why keep dataclass instead of Pydantic?** Preserves exact legacy error messages and avoids
  pulling validation framework semantics into the crypto boundary.
