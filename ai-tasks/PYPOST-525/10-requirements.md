# PYPOST-525: Per-environment failure reporting for encryption migration

## Goals

PYPOST-487 delivered encryption migration tooling so operators can verify decrypt access,
encrypt plaintext hidden values, and bulk re-encrypt stored environments during key-source or
rotation rollouts. That tooling must report which stored environments fail to decrypt so
operators can fix key material or data issues before rewriting files.

Today the migration path reaches into unsupported storage internals because the standard
environment-loading path hides individual failures and returns no per-environment detail.
This coupling increases maintenance risk: storage changes can break migration without a clear
contract, and operators lose actionable diagnostics when only some environments are bad.

This task establishes supported storage capabilities for loading stored environments with
per-item failure reporting, and removes the migration tool's dependence on private storage
internals. The outcome is a maintainable boundary between persistence and migration tooling,
with unchanged behavior for normal desktop use.

## Programming Language

Python 3.10+

## User Stories

- As an operator running encryption migration verify, I want failures attributed to specific
  stored environments so I know which entries need key or data fixes before re-encrypt.
- As an operator running bulk re-encrypt or encrypt-plaintext, I want the same per-environment
  failure detail when decrypt fails partway through so I can abort safely without guessing.
- As a maintainer, I want migration tooling to use only supported storage interfaces so future
  storage refactors do not silently break encryption migration.
- As a desktop user opening the application, I want environment loading to behave as today when
  some or all stored environments cannot be read — this task must not regress normal app startup
  or environment selection behavior.

## Definition of Done

- Stored environments can be loaded through a supported public storage capability that returns
  successfully loaded environments together with per-environment failure information (environment
  identity and a human-readable reason).
- Encryption migration tooling no longer depends on private storage internals to obtain that
  per-environment failure detail.
- Verify, bulk re-encrypt, and encrypt-plaintext migration flows continue to produce the same
  operator-visible outcomes as before (success, skip, or failure with actionable error list).
- Normal desktop environment loading from the application UI is unchanged in observable behavior
  for end users.
- Automated tests cover the new supported loading capability and confirm migration uses it.
- Out-of-scope items below are not expanded by this task.

## Task Description

Source: [PYPOST-487 technical debt TD-1](ai-tasks/PYPOST-487/60-tech-debt.md). Follow-up Jira:
[PYPOST-525](https://pypost.atlassian.net/browse/PYPOST-525).

### Problem

Encryption migration must decrypt every stored environment to verify access or rewrite ciphertext.
When one environment fails (missing key, corrupt data, invalid shape), operators need a report
naming that environment and the failure reason. The standard storage load path used by the
desktop UI is optimized for resilience: any failure results in no environments loaded, with no
per-item breakdown. Migration therefore bypasses that path via unsupported internal access, which
is technical debt from PYPOST-487 Step 6.

### In Scope

- Business requirement for a supported way to load stored environments while collecting
  per-environment failures without aborting the whole batch on the first bad entry.
- Migration tooling adoption of that supported capability; removal of private storage coupling.
- Preservation of existing end-user environment load behavior.
- Test coverage for the new capability and migration integration.

### Out of Scope

- Changing how the desktop UI presents load failures to end users.
- Other PYPOST-487 follow-ups (Settings UI migration actions, CLI `--json`, inventory
  data-quality flags, `build_inventory(check_decrypt=True)` unification, no-op re-encrypt
  skip, keyring integration tests, operator runbook updates).
- New migration features, envelope format changes, or key-provider behavior changes.

### Constraints and Assumptions

- Stored environments remain in the existing on-disk format; this task addresses how they are
  loaded for migration, not what is stored.
- Per-environment errors concern decrypt and deserialize failures for individual environment
  records, consistent with current migration reporting (environment name plus message).
- Operators may still have environments that load successfully alongside failed ones; migration
  should continue to treat any decrypt failure as operation failure while listing all failures.
- Assumes PYPOST-487 migration service and CLI remain the primary consumers; no new user-facing
  product surface beyond supported storage access.

### Main Entities (Business Perspective)

| Entity | Role | Key attributes |
| --- | --- | --- |
| Stored environment | Named persisted configuration used for HTTP requests and variable management | Display name; variable definitions (plain and hidden); hidden values that may be encrypted at rest; on-disk record identity used in failure reports |
| Storage manager | Product component responsible for reading and writing stored environments | Supported load/save contract; batch-oriented load with per-item outcomes; separation between desktop-oriented and migration-oriented load behavior |
| Encryption migration service | Operator-facing capability to verify, encrypt, and re-encrypt stored secrets during key rollout | Verify, encrypt-plaintext, and bulk re-encrypt operations; dependency on supported storage loading only |
| Migration report | Outcome of a migration operation presented to the operator | Operation success flag; environment inventory; list of operator-readable per-environment errors (identity and reason) |
| Operator | Administrator or maintainer running migration verify or rewrite commands | Runs CLI or service-backed migration; interprets per-environment failure lists before re-encrypt |
| Desktop user | End user who selects and edits environments in the application UI | Unaffected by migration-oriented loading; continues to use existing environment selection and startup behavior |

### Interactions

1. Operator invokes migration verify or rewrite → migration service requests stored environments
   through supported storage loading with per-item error collection.
2. Storage returns successfully loaded environments and failure details for any entries that
   could not be deserialized or decrypted.
3. Migration service aggregates failures into the migration report; operator sees which
   environments failed and why.
4. Desktop user opens the app → UI continues to use the existing load path with unchanged
   resilience behavior.

## Functional Requirements

- The product must provide a supported storage capability to load stored environments while
  collecting per-environment failures without stopping the batch on the first bad entry.
- That capability must return successfully loaded environments together with per-environment
  failure details: environment identity and a human-readable reason for each failed entry.
- Encryption migration tooling must obtain per-environment failure detail only through supported
  storage interfaces; private storage internals must not be required.
- Migration verify, bulk re-encrypt, and encrypt-plaintext flows must continue to produce the
  same operator-visible outcomes as today (success, skip, or failure with an actionable error
  list naming affected environments).
- Desktop environment loading for normal application use must behave as today when some or all
  stored environments cannot be read (startup, selection, and resilience semantics unchanged).
- Per-environment failures must cover decrypt and deserialize errors for individual environment
  records, consistent with current migration reporting.
- Automated tests must cover the supported loading capability and confirm migration tooling uses
  it.

## Non-functional Requirements

- **Safety**: migration operations must not publish partial or corrupted environment storage;
  failed migration attempts must leave prior on-disk data recoverable; per-environment failure
  reports must not expose key material.
- **Backward compatibility**: legacy stored environment files and existing desktop load behavior
  remain unchanged until operators run migration tooling that uses the new capability.
- **Operability**: per-environment failure messages must be sufficient for operators to identify
  which stored environments need key or data fixes without reading implementation details.
- **Maintainability**: migration tooling must depend on a documented supported storage contract so
  future storage refactors do not silently break encryption migration.

## Stakeholder Approval

Approved via sprint-task-runner autonomous mode (2026-06-11).

## Q&A

| Question | Answer |
| --- | --- |
| Why is a new supported loading capability needed instead of changing the existing UI load path? | The UI path prioritizes a simple outcome for end users (show what loaded, log failures). Migration needs a batch-oriented outcome: list every failure while still processing remaining environments. Changing UI behavior could affect startup and selection; this task adds a supported migration-oriented contract without forcing that trade-off on desktop users. |
| Why was private storage access acceptable in PYPOST-487? | It was a deliberate shortcut to ship migration tooling on time. Step 6 identified it as medium-priority debt (TD-1) because it couples migration to storage internals. |
| Must migration behavior change for operators? | No. Verify and rewrite commands should report the same success, skip, and error outcomes; only the internal coupling is removed. |
| What counts as a per-environment failure? | Same cases migration already surfaces: decrypt errors for a named stored environment (e.g. missing key material for that environment's ciphertext). File-level or whole-file parse failures remain outside per-item reporting unless already handled elsewhere. |
