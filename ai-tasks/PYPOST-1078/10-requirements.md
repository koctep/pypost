# PYPOST-1078: Add failure-path lifecycle UI coverage for encryption migration worker

## Goals

From a software reliability and quality perspective, the application's background migration workflow must deterministically handle unexpected failures without crashing, leaking threads, leaving the user interface locked, or failing to inform the user. Adding deterministic automated test coverage specifically for the worker failure path verifies that upon emitting an error signal, the application cleans up memory safely, re-enables interactive controls, and delivers clear error messaging to the operator.

## User Stories

- **As an Application Operator**, when an encryption migration operation fails unexpectedly, I want the application to remain stable, display a clear failure message, and immediately restore the user interface so that I can take corrective action.
- **As a Developer / Maintainer**, I want deterministic unit test coverage of the migration worker failure lifecycle that does not depend on slow OS threads or live storage IO, ensuring fast, reliable CI test execution.

## Definition of Done

- A deterministic test case exercises the background worker failure lifecycle sequence (`failed(message)` followed by `finished()`).
- Test verifies that the worker instance is strongly retained during execution and properly cleaned up (`deleteLater`) after the failure event.
- Test verifies that the failure dialog is displayed with the failure details.
- Test verifies that migration action buttons are re-enabled following the failure.
- Test runs deterministically with bounded cleanup and explicit timeout.

## Task Description

- **Implementation Language**: Python
- **Problem**: Follow-up from PYPOST-1072. Existing UI tests verified worker retention and cleanup during successful migration runs (`succeeded` -> `finished`), but lacked dedicated deterministic UI assertions covering the failure lifecycle path (`failed` -> `finished`).
- **Business Scope & Boundaries**:
  - Add deterministic failure-path lifecycle test coverage for the encryption migration UI.
  - Avoid flaky OS thread scheduling or live filesystem/crypto dependencies by utilizing deterministic test fixtures.
  - Exclude production changes unless a lifecycle gap is uncovered during verification.
- **Business Domain Entities**:
  - *Migration Worker*: Background execution task responsible for performing secret migrations.
  - *Worker Failure Event*: Signal indicating an unhandled exception or abort during migration.
  - *Failure Notification*: User-facing modal alerting the operator to the migration error.

## Q&A

- **Q**: Does this require modifications to production code?
  - **A**: No, the production failure handling logic is in place; this task adds deterministic test coverage to prevent future regressions.
