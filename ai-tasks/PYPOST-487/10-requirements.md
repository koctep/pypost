# PYPOST-487: Evaluate migration from env-var-only key source to configurable key provider strategy

## Goals

Environment encryption at rest (PYPOST-447) began with a single key supplied through process
environment variables. User-facing encryption settings (PYPOST-481) and flexible key resolution
with rotation (PYPOST-483) expanded how key material can be obtained, but many deployments still
rely on the original environment-variable path. Without a defined migration and rollout plan,
administrators cannot safely adopt stronger key-management options, change encryption settings on
existing data, or understand what fallback behavior means in production.

This task defines business requirements for evaluating and delivering a migration path away from
env-var-only key sourcing, staged rollout of secure provider options, and operator-facing
documentation of operational requirements and fallback behavior. The outcome must reduce data-loss
risk during transitions and give teams a predictable path from legacy setups to configurable key
provider strategies.

## Programming Language

Python 3.10+

## User Stories

- As a security-conscious administrator, I want a documented migration path from
  environment-variable keys to a preferred secure provider so I can adopt stronger key management
  without losing access to existing encrypted environment data.
- As an administrator planning a team rollout, I want evaluated rollout stages for secure provider
  options so I can phase adoption by risk, readiness, and operational maturity.
- As an administrator changing encryption settings, I want clear operational steps and safeguards
  so enabling encryption, changing key source, or rotating keys does not silently corrupt or strand
  environment secrets.
- As a desktop user enabling encryption for the first time, I want existing hidden secret values to
  become protected at rest without manually re-entering every secret.
- As an administrator who has rotated encryption keys, I want an optional path to re-encrypt stored
  values under the current active key so long-term storage does not depend indefinitely on retired
  key material.
- As an existing user on an environment-variable-only setup, I want upgrades to remain
  backward-compatible so I am not forced to migrate until I choose to.
- As an operator, I want documented fallback behavior when a preferred key source is unavailable so
  I know whether the application will recover, fail safely, or require intervention.
- As a maintainer supporting deployments, I want operational requirements documented (prerequisites,
  verification, rollback expectations) so migration incidents are diagnosable without reading
  implementation details.

## Definition of Done

- Business requirements define migration paths for moving from env-var-only key sourcing to
  configurable key provider strategies supported by the product.
- Secure provider options are evaluated at a business level with recommended rollout stages
  (who should use which option when, and what must be true before advancing).
- Operational requirements are documented for each major migration scenario (at minimum: adopting a
  new key source, enabling encryption on existing plaintext hidden values, changing primary key
  source, key rotation with optional bulk re-encryption).
- Fallback behavior is documented for operators: what happens when primary or configured fallback
  sources do not yield key material, and what safe failure looks like to users.
- Acceptance criteria verify that migration guidance preserves read access to existing encrypted
  data and does not require mandatory migration for legacy deployments.
- Out-of-scope items are explicit so provider implementation and unrelated performance work are not
  conflated with this task.
- Deliverables from later steps (architecture, tooling, operator docs) trace back to these
  requirements.

## Task Description

Source: [PYPOST-447 technical debt — Follow-up Tasks](
https://pypost.atlassian.net/browse/PYPOST-447). PYPOST-481 exposed encryption policy and key
source preferences in application settings. PYPOST-483 delivered configurable key resolution from
multiple secure source categories and a supported key rotation lifecycle. Technical debt remains:
there is no consolidated migration plan for teams still on env-var-only setups, no evaluated
rollout guidance for choosing among provider options, and no operator runbook for settings changes
that affect existing persisted environment data (including optional bulk re-encryption after
rotation).

### In Scope

- Business requirements for migration away from env-var-only key sourcing toward configurable key
  provider strategies already supported by the product.
- Evaluation of secure provider options and recommended rollout stages (individual desktop,
  small team, centrally managed secrets).
- Operational requirements for migration scenarios:
  - adopting a non-environment primary key source while retaining decrypt access to existing data;
  - enabling encryption at rest when hidden values are currently stored in plain text;
  - changing primary key source or fallback order with existing encrypted data;
  - completing key rotation with optional bulk re-encryption of stored values;
  - verifying migration success and safe rollback expectations before retiring old key material.
- Operator-facing documentation requirements for fallback behavior when configured sources fail or
  yield incomplete key material.
- Backward compatibility: legacy env-var-only deployments continue to work without mandatory
  migration.
- Prerequisites and verification checkpoints operators must satisfy before and after each migration
  stage (for example: backup, decrypt verification, confirm new encryption on save).

### Out of Scope

- Implementing new key provider backends beyond those delivered in PYPOST-483 (for example,
  additional vault integrations tracked separately).
- Selecting or contracting with specific third-party secret-management vendors.
- Changing encryption algorithms, envelope format, or key-identifier rules.
- Full Settings UI redesign unrelated to migration guidance or optional migration actions.
- Performance optimizations for encryption load/save (PYPOST-485, PYPOST-486).
- Automatic mandatory re-encryption on every settings change without operator intent or
  documented safeguards.

## Functional Requirements

- The product must support a documented migration path from env-var-only key sourcing to each
  configurable key provider strategy the product offers.
- Migration guidance must preserve read access to environment data encrypted before the migration
  while historical key material remains available per the rotation model from PYPOST-483.
- Operators must be able to enable encryption at rest on existing deployments such that previously
  plain-text hidden values become encrypted without requiring users to re-enter secrets manually.
- Operators must be able to change primary key source or fallback order with a defined procedure
  that avoids silent data loss.
- Operators must have an optional, explicit path to bulk re-encrypt stored values under the
  current active key after rotation, so retired key material can be removed when no longer needed.
- Rollout stages must state prerequisites, target audience, and go/no-go criteria for advancing
  from one key-management maturity level to the next.
- Fallback behavior must be documented: when a preferred source is unavailable, which configured
  alternatives are attempted, when the application stops with a safe error, and what the user
  experiences.
- Legacy deployments that use only process environment variables for key material must continue to
  operate without forced migration.
- Migration failures must surface clear, safe errors without exposing key material.

## Non-functional Requirements

- **Safety**: migration procedures must not publish partial or corrupted environment storage; failed
  migration attempts must leave prior data recoverable where rollback is documented.
- **Backward compatibility**: unchanged legacy setups behave as before until an operator initiates
  migration or changes settings.
- **Operability**: migration and fallback documentation must be sufficient for administrators
  without access to source code.
- **Security**: operational guidance must reinforce that key material stays outside application
  settings files and that retiring historical keys too early causes permanent decrypt loss for
  values still tied to those keys.
- **Traceability**: rollout stages and migration steps must be verifiable (pre- and post-checks
  documented at a business level).

## Constraints and Assumptions

- PYPOST-447 encryption-at-rest, PYPOST-481 application settings, and PYPOST-483 multi-source key
  resolution and rotation are available as the baseline capability.
- Supported key source categories are process environment variable, OS-integrated keyring, and
  external secret store, as established in PYPOST-483.
- Application settings select strategy and fallback order but do not store raw encryption key
  material.
- Mixed key identifiers in persisted environment data after rotation are expected until optional
  bulk re-encryption is performed.
- Python 3.10+ is used for any migration tooling delivered in later steps.
- Project documentation standards (English, 100-character line length for markdown artifacts)
  apply.

## Main Entities and Interactions

- **Encryption policy**: whether hidden environment values are encrypted at rest.
- **Key source strategy**: where the product resolves encryption key material (primary and
  fallback order).
- **Key registry / rotation state**: active key for new encryption and historical keys needed to
  read existing encrypted values.
- **Persisted environment storage**: on-disk environment data that may contain plain-text hidden
  values, encrypted values, or a mix of key identifiers after rotation.
- **Migration procedure**: operator-defined sequence to move from one key-management posture to
  another without losing data access.
- **Rollout stage**: recommended maturity level describing which provider options suit which
  deployment context and what must be verified before adoption.
- **Operator**: plans migration, configures key material in secure stores, runs verification, and
  optionally triggers bulk re-encryption.
- **Desktop user**: benefits from encryption and migration outcomes; may initiate settings changes
  that require operator follow-through for safe migration.

Interaction overview:

1. Operator assesses current key-management posture and selects a target rollout stage.
2. Operator satisfies documented prerequisites (key material provisioned, fallback configured,
   backup and decrypt verification).
3. Operator or user changes encryption settings or key source strategy per documented procedure.
4. Application resolves keys through configured provider strategy; fallback behavior applies when
  sources are incomplete or unavailable.
5. On save/load, environment storage reflects encryption policy; optional bulk re-encryption
   consolidates values under the current active key when the operator chooses that path.
6. Operator verifies success; historical key material is retired only after documented checks pass.

## Q&A

- Q: Why is this separate from PYPOST-483?
  A: PYPOST-483 delivered multi-source resolution and rotation capability. PYPOST-487 defines how
  teams migrate from legacy env-var-only setups, evaluate rollout stages, and operate settings
  changes safely on existing data—including optional bulk re-encryption deferred from PYPOST-483.
- Q: Must every deployment migrate off environment variables?
  A: No. Environment-variable sourcing remains supported. Migration is optional and staged for
  teams that need stronger key management.
- Q: Is bulk re-encryption required after every key rotation?
  A: No. Rotation is complete when new encryption uses the active key and historical keys remain
  available for existing values. Bulk re-encryption is an optional operator step to retire old
  key material and normalize stored data under the current key.
- Q: What happens if an operator changes key source before provisioning key material in the new
  source?
  A: The product must fail safely with clear errors; migration documentation must list prerequisites
  so operators configure the new source before cutover.
- Q: What if fallback sources are configured but none yield an active key?
  A: Documented fallback behavior must state that save/load cannot proceed for encrypted data until
  key material is restored; users see safe errors consistent with existing encryption failure
  expectations from PYPOST-447.
- Q: Does this task add new provider types?
  A: No. It evaluates and documents migration and rollout for provider categories already in scope
  of PYPOST-483; new backends are tracked separately (for example PYPOST-500).
- Q: Who performs migration—end user or administrator?
  A: Settings changes may be made by desktop users, but provisioning key material, verifying
  decrypt access, and optional bulk re-encryption are administrator/operator responsibilities;
  requirements must distinguish user-initiated settings from operator migration steps.
