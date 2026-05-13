# PYPOST-447: Optional encrypted-at-rest storage for sensitive environment values

## Goals

Define requirements for protecting sensitive environment variable values at rest while keeping
the product usable and backward-compatible with existing plain-text environment data.

## Programming Language

Python

## User Stories

- As a security-conscious user, I want secret environment values to be encrypted on disk so local
  file access does not reveal plain-text secrets.
- As an existing user, I want old `environments.json` files to continue loading so I can upgrade
  without data loss.
- As a developer, I want a clear key-management policy so encryption behavior is predictable and
  supportable.
- As a maintainer, I want explicit decryption boundaries so secrets are only decrypted where
  required for runtime execution.

## Definition of Done

- Step 1 requirements define threat model assumptions and explicit security goals.
- Requirements define supported key-management approaches and selection criteria.
- Requirements define backward-compatible migration expectations for existing plain-text data.
- Requirements define runtime decryption boundaries and prohibited exposure surfaces.
- Requirements define acceptance criteria and required test categories.
- Out-of-scope items are explicit to avoid accidental architecture decisions in Step 1.

## Task Description

This task follows `PYPOST-437`, where hidden variables were introduced as a display-level
protection. Hidden flags do not protect values at rest, so secrets may still be stored in
plain text in environment storage.

The task must establish requirements for optional encryption-at-rest for sensitive environment
values, including how keys are managed, how current data is migrated safely, and where decrypted
data is allowed at runtime.

### In Scope

- Requirements for optional encryption-at-rest of sensitive environment variable values.
- Threat model and security objectives for local storage risks.
- Key-management options and constraints.
- Backward-compatible migration behavior from existing plain-text storage.
- Runtime decryption boundaries and verification expectations.

### Out of Scope

- Final cryptographic algorithm choice and implementation details.
- Concrete architecture diagrams and component-level design.
- UI redesign unrelated to encryption configuration.
- Cloud key vault integration unless needed by approved architecture in Step 2+.
- Changes unrelated to sensitive environment value storage.

## Functional Requirements

- The system must support optional encryption for sensitive environment variable values at rest.
- The system must preserve loading of existing plain-text environment data without manual edits.
- The system must provide deterministic behavior for mixed data states (plain and encrypted) during
  migration periods.
- The system must define how sensitive values are identified for encryption eligibility.
- The system must define failure behavior when decryption is not possible (missing key, corrupted
  payload, or invalid format).
- The system must define safe handling for export/import and cloning operations that include
  sensitive values.

## Non-functional Requirements

- Security: reduce risk of local secret disclosure from storage file access.
- Backward compatibility: avoid breaking existing projects and environment files.
- Reliability: encrypted data must be readable across application restarts when key material is
  available.
- Usability: encryption behavior should not degrade normal request execution workflows.
- Maintainability: requirements must enable testable and auditable implementation in later steps.

## Constraints and Assumptions

- Existing `environments.json` data format is currently used in deployed workflows.
- Hidden-variable behavior from `PYPOST-437` remains a display concern and is not sufficient for
  at-rest protection.
- Step 1 defines requirements only and does not lock implementation details.
- Security requirements must prioritize preventing secret leakage over convenience defaults.
- Project-wide markdown and line-length rules apply to all generated artifacts.

## Main Business Entities and Interactions (Business View)

- Environment storage: persistent file-based storage for environment definitions and values.
- Sensitive environment value: environment variable value requiring stronger at-rest protection.
- Encryption key material: secret used to encrypt/decrypt protected values.
- Runtime execution context: request execution flow that consumes resolved variable values.
- Migration process: transition path from plain-text values to encrypted storage.

Interaction overview:

1. User has existing environment data that may include sensitive values.
2. Encryption-at-rest can be enabled under defined requirements.
3. Migration logic processes existing data while preserving compatibility.
4. Runtime resolves values and decrypts only within approved boundaries.
5. Logging/history behavior must continue to avoid exposing raw sensitive values.

## Acceptance Test Expectations (Step 1 Level)

- Compatibility tests for loading legacy plain-text environments.
- Migration behavior tests for plain-to-encrypted transitions.
- Runtime boundary tests confirming decryption occurs only in approved paths.
- Error-path tests for missing or invalid key material.
- Regression tests ensuring non-sensitive variables keep existing behavior.

## Q&A

- Q: Why is this needed if hidden variables already exist?
  A: Hidden flags protect display surfaces, but do not protect values stored on disk.
- Q: Must all environment values be encrypted?
  A: No. Requirement is optional encryption focused on sensitive values.
- Q: Can we choose implementation details now?
  A: No. Step 1 captures requirements; architecture and concrete design come in Step 2.
