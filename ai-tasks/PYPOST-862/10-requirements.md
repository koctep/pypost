# PYPOST-862: Caplog coverage for agent e2e seed write failure

## Goals

Maintainers need automated proof that when seeded-workspace persistence fails,
the failure is visible in logs under a stable event name and the error is not
swallowed. Today success-path seed coverage exists (PYPOST-857), but the
failure path is not asserted under the project's error-path logging contract.
Closing this gap reduces silent seed failures in agent e2e setups and makes
regressions in failure handling detectable in CI.

## Programming Language

Python 3.10+

## User Stories

- As a **maintainer**, I want an automated check that a seed write failure
  emits the documented failure event and still surfaces the error, so agent e2e
  seed problems are diagnosable and not quietly ignored.
- As a **contributor**, I want that check to follow the same timeout and
  error-path logging rules as other pytest modules, so new failure-path tests
  stay consistent with the suite.
- As a **desktop user** (indirect), I want this debt work not to change how
  seeding behaves for successful writes—only to lock in failure-path
  observability and propagation already expected by the seed contract.

## Definition of Done

- An automated unit/integration check forces a persist failure during seed
  write, asserts the failure log event `agent_e2e_seed_failed`, and confirms
  the exception propagates (is re-raised).
- The check uses the project's error-path logging capture approach (caplog) for
  the seed fixture logger.
- The check declares an explicit pytest timeout marker (module, class, or
  function scope).
- Steps 1–8 task artifacts exist for PYPOST-862.
- No intentional change to successful seed inventory or user-visible product
  UX beyond locking the failure-path contract.

## Task Description

**Problem:** PYPOST-857 delivered builders and `write_agent_e2e_seed` with
success logging and a failure log event, but Step 7 noted optional missing
coverage: force StorageManager/persist failure, assert
`agent_e2e_seed_failed` under caplog, and confirm re-raise (do-testing C1).
Source: [PYPOST-862](https://pypost.atlassian.net/browse/PYPOST-862), from
[PYPOST-857](https://pypost.atlassian.net/browse/PYPOST-857)
`ai-tasks/PYPOST-857/60-tech-debt.md`.

**Business need:** Close this low-priority testing debt so seed write failures
remain observable and non-silent under automated verification.

### In Scope

- Adding one focused automated check for seed write failure logging + re-raise.
- Using mocks or equivalent isolation so the check does not depend on live
  external services.
- Completing Steps 1–8 workflow artifacts.

### Out of Scope

- Changing seed inventory contents, builders, or success-path GUI proofs.
- Broader agent e2e packaging (PYPOST-858), HTTP determinism (PYPOST-859),
  failure artifacts (PYPOST-860), or make/CI pack entry (PYPOST-861).
- Optional drive-then-snapshot / resolve proofs (PYPOST-863) or inventory
  drift guards (PYPOST-864).
- New product features or UI changes.

## Functional Requirements

- FR1: When seed persistence fails, the automated check records that the
  failure event `agent_e2e_seed_failed` was logged.
- FR2: When seed persistence fails, the automated check records that the
  underlying exception still propagates to the caller.
- FR3: The check isolates persistence failure without requiring a live
  network or full GUI session.
- FR4: The check participates in the existing seed test surface (same module
  family as PYPOST-857 seed tests) so maintainers can discover it with other
  seed coverage.

## Non-Functional Requirements

- NFR1: Explicit pytest timeout marker on the new check (or inherited module
  marker).
- NFR2: Caplog (or equivalent project-allowed) assertion of the ERROR-path
  event for the seed fixture logger.
- NFR3: Fast, deterministic unit/integration style (mocked I/O preferred).
- NFR4: No secrets or live host dependency in the failure scenario.

## Constraints and Assumptions

- Seed writer and failure event name already exist from PYPOST-857; this task
  primarily adds verification.
- Exception type used to force failure may be a generic persist/IO error;
  exact storage internal exception class is not a business requirement.
- Autonomous batch run: user approval gates are pre-approved for Steps 1–8;
  Jira updates and git commit are out of band for this execution.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Seeded workspace | Documented collections/environments written before agent e2e session start |
| Seed write failure | Persist error while writing that workspace |
| Failure log event | Named log signal that seed write failed |
| Caller | Test or helper that invoked seed write and must see the error |

## Q&A

- Q: Why is this needed if seed success is already tested?
  A: Success coverage does not prove failure logging or that errors propagate;
  silent catch would break agent e2e diagnostics.
- Q: Is a full GUI session required?
  A: No. Business need is the seed write failure contract; isolation without a
  full session is preferred.
- Q: Source of the debt item?
  A: [PYPOST-857 tech debt](../PYPOST-857/60-tech-debt.md) — Caplog coverage
  for seed write failure → [PYPOST-862](https://pypost.atlassian.net/browse/PYPOST-862).
