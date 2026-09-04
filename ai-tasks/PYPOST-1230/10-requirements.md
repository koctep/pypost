# PYPOST-1230: Extract a shared presenter import lifecycle wait helper

## Goals

Presenter tests exercise asynchronous collection imports. They currently keep the import-specific
waiting contract inside one test module, even though other presenter suites need the same lifecycle
coordination. This makes the behavior harder to discover and creates a risk that future suites will
wait for only part of an import, producing flaky assertions or teardown races.

The business goal is to provide one reusable test-support contract for recognizing that an import
scenario is genuinely complete. A test should continue only after its expected outcome has occurred
and the related presenter import interaction has returned to an idle state. This improves test
determinism and lets future presenter suites use the same definition of completion.

This is a test-maintainability task. It must not change the collection import experience or any
runtime behavior of the application.

## User Stories

- As a developer writing presenter tests, I want a reusable way to wait for an asynchronous import
  outcome and its lifecycle completion, so that my assertions run at a deterministic point.
- As a maintainer of the import test suite, I want the completion contract defined in one shared
  place, so that lifecycle changes do not require finding and updating copied test logic.
- As a developer adding another asynchronous presenter test suite, I want to use the established
  import-waiting behavior without depending on a helper that is private to a different test module.
- As a reviewer of asynchronous tests, I want timeout failures to be bounded and explicit, so that a
  stalled import is reported as a test failure rather than hanging the suite.

## Definition of Done

- A shared test-support capability exists for presenter import lifecycle waits and is available to
  presenter test suites.
- The shared capability preserves the existing completion contract: it waits for both the test's
  expected outcome condition and the import presenter to become idle before returning.
- Waiting remains bounded by a caller-selectable timeout with a clear failure when completion does
  not occur within that period.
- The existing collection import UI tests use the shared contract and retain their current
  assertions and scenario coverage.
- The shared contract can be reused by other presenter test suites without copying the import
  lifecycle logic.
- No production application behavior, public presenter behavior, dialogs, status messages, import
  results, or persistence behavior changes as a result of this task.
- The task does not introduce a new import lifecycle requirement; it centralizes test coordination
  for behavior that already exists.

## Task Description

### Problem

The collection import UI tests need to observe asynchronous work. Their local waiting behavior
combines two business-relevant test conditions: the scenario's expected result is visible, and the
presenter has finished all import activity. Keeping that contract local prevents reuse and makes it
easy for a second suite to accidentally assert while work is still finishing.

### Scope

In scope:

- Define the shared test-support contract for waiting on a presenter import scenario.
- Make the existing collection import UI tests consume that shared contract.
- Preserve the current success, error, conflict, and completion timing expectations of those tests.
- Make the shared capability suitable for reuse across presenter test suites.

Out of scope:

- Changes to production collection-import code or presenter runtime APIs.
- Changes to worker cancellation, thread behavior, presenter lifecycle state, or teardown policy.
- New user-facing import features, dialogs, messages, persistence behavior, or performance goals.
- Rewriting unrelated test waiting helpers or changing the test framework's general event-loop
  policy.
- Adding new product behavior solely to make the test-support contract possible.

### Constraints and Assumptions

- The implementation language is Python, matching the existing application and test suite.
- Existing asynchronous import tests are the source of truth for behavior that must be preserved.
- A scenario may be considered complete only when its expected result has occurred and the import
  interaction is no longer active.
- A stalled or incomplete scenario must fail within its configured time bound and identify that the
  completion condition was not met.
- This task is intended to reduce duplication and drift; it is not permission to broaden the scope
  into unrelated test infrastructure.

### Non-Functional Requirements

- Determinism: the shared contract must provide the same lifecycle synchronization guarantees as
  the existing collection import tests.
- Boundedness: no waiting operation may leave the test suite indefinitely blocked when completion
  does not happen.
- Reusability: the contract must be understandable and usable by independent presenter test
  suites.
- Maintainability: future lifecycle-waiting changes should have one clearly owned test-support
  location.
- Compatibility: the extraction must not alter application runtime behavior or require production
  callers to adopt a new API.

## Main Entities

- **Collection import scenario**: one test-driven import interaction, including successful,
  invalid-input, conflict, or other terminal outcomes.
- **Presenter import interaction**: the business process whose completion is being observed; it is
  complete only after the expected outcome and final idle condition are both true.
- **Presenter test suite**: a collection of automated scenarios that needs a consistent completion
  contract when exercising asynchronous presenter behavior.
- **Shared lifecycle-wait contract**: the reusable test-support behavior that coordinates scenario
  completion and reports a bounded failure when completion cannot be established.

## User Scenarios

1. **Successful import**: a test starts an import and waits until the expected result is shown and
   the presenter has finished the import interaction before checking persisted collections or the
   refreshed view.
2. **Invalid import**: a test starts an import with invalid content and waits until the expected
   error outcome is shown and the presenter is idle before checking that data was not changed.
3. **Conflict resolution**: a test exercises an import that requires conflict handling and waits
   until the expected result and final lifecycle completion are both observable.
4. **Slow or stalled import**: a test whose completion condition is not reached fails within the
   configured timeout and exposes a useful timeout indication instead of hanging.
5. **Reuse by another presenter suite**: a future presenter test suite adopts the shared contract
   and receives the same definition of completed asynchronous work without duplicating the local
   import test logic.

## Q&A

- **Q: Why is extracting this behavior valuable if it does not change the application?**

  A: Asynchronous presenter tests are only reliable when they observe the complete interaction.
  Centralizing the contract reduces copied logic, prevents suites from making inconsistent
  assumptions, and makes failures easier to diagnose.

- **Q: What does the test need to wait for?**

  A: Both conditions are required: the caller's expected scenario outcome must have occurred, and
  the associated import interaction must be idle. Either condition alone can allow assertions to
  run too early.

- **Q: Does this task change what application users see?**

  A: No. It changes only how automated presenter tests coordinate with existing asynchronous
  behavior.

- **Q: Does this task include worker cancellation or presenter lifecycle refactoring?**

  A: No. Those are separate technical-debt concerns. This task only makes the existing test wait
  contract reusable.

- **Q: What is the implementation language?**

  A: Python, because the relevant application and presenter test suites are Python-based.

- **Q: What is the source of the task?**

  A: Jira PYPOST-1230, created from the presenter test-helper coupling follow-up in
  `ai-tasks/PYPOST-1182/60-tech-debt.md`.
