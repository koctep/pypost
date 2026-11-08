# PYPOST-1451: Discovery Failure and Retry Automated Coverage

## Goals

When importing collection variables, users rely on PyPost's ability to discover and enumerate remote library collections alongside existing local workspace collections. Catalog discovery runs asynchronously in the background so that the dialog opens immediately without freezing the UI.

In PYPOST-1450, dedicated discovery status feedback and error controls were established separately from collection-fetch loading chrome. However, the system currently lacks comprehensive automated test coverage for failure modes, retry recovery, and cancellation edge cases in this background discovery lifecycle.

Without rigorous automated test coverage for discovery failure and retry flows:
- Network failures, server errors, or misconfigured connections during catalog enumeration could regress silently, leading to unhandled exceptions or frozen dialog states.
- Users could be left without actionable feedback or unable to retry discovery when transient network issues resolve.
- External service failures could unintentionally block or degrade access to local workspace collections.
- Rapid retries, generation mismatches, or dialog closure could introduce race conditions, stale catalog entries, or background worker thread leaks.

The goal of this task is to establish comprehensive automated test coverage for discovery failure handling, error feedback presentation, retry recovery, and background worker lifecycle management.

## User Stories

1. **Clear Failure Feedback**: As a user opening the Import Collection Variables dialog when a remote connection is offline or failing, I want to see a clear, non-intrusive discovery failure message and a retry action, so that I understand why remote collections are not listed without the dialog crashing or hanging.
2. **Unimpeded Workspace Collections**: As a user with local workspace collections, when background remote catalog discovery fails, I want to continue browsing, selecting, and importing variables from my local collections without interruption, so that external connection problems do not stop local work.
3. **Seamless Retry Recovery**: As a user whose remote discovery failed due to a transient issue, when I click Retry after the issue resolves, I want the discovery operation to restart, clear the previous failure message, and populate the remote collections upon success.
4. **Resilience to Repeated or Stale Retries**: As a user who triggers retry or closes the dialog while discovery is in-flight, I want cancelled or stale discovery operations to be cleanly discarded without causing stale data insertion, UI flicker, or resource leaks.

## Definition of Done

- **Discovery Failure Verification**:
  - Automated tests verify that when catalog discovery encounters an error (e.g. connection listing failure or manifest retrieval failure), the error is caught safely and does not propagate unhandled.
  - Automated tests verify that a dedicated failure notification is presented to the user with an actionable retry control.
- **Workspace Collection Isolation**:
  - Automated tests verify that local workspace collections remain fully selectable and their variables importable even while remote discovery is in a failed state.
- **Retry Lifecycle Verification**:
  - Automated tests verify that triggering retry from a failed state clears the error notification and initiates a new discovery attempt under an incremented lifecycle generation.
  - Automated tests verify that when a retried discovery succeeds, the newly discovered collections are populated into the collection selection options and the status display updates accordingly.
- **Cancellation & Generation Robustness**:
  - Automated tests verify that intermediate cancellations or rapid retries discard results from outdated discovery generations.
  - Automated tests verify that closing the dialog or cancelling in-flight discovery terminates background workers cleanly without memory or thread leaks.
- **Repository Quality Compliance**:
  - All new tests follow project testing guidelines (bounded timeouts, deterministic waits, clean cleanup).
  - All tests pass via `make check`.

## Task Description

This task focuses on building automated test coverage for the failure and recovery paths of background remote catalog discovery in the Import Collection Variables dialog.

### Scope and Boundaries

- **In Scope**:
  - Automated unit and integration tests for catalog discovery failure handling.
  - Automated tests for discovery status UI transitions (in-progress, failed, retrying, succeeded).
  - Automated tests for discovery retry workflows, verifying generation tracking and successful catalog population after recovery.
  - Automated tests for edge cases including worker cancellation, stale result rejection, and clean teardown on dialog close.
- **Out of Scope**:
  - Redesigning the visual layout of the Import Collection Variables dialog (established in PYPOST-1450).
  - Modifying backend server catalog protocols or remote library storage formats.
  - Changing collection variable parsing, merging, or preset selection logic.

### Constraints & Assumptions

- The implementation language is Python.
- All tests must execute cleanly within the existing test framework and pass `make check`.
- Tests must not rely on live network services; mock or stub library connections must be utilized to simulate both deterministic failures and recovery.
- Automated tests must run fast and reliably without unbounded thread sleeps or flaky timing assumptions.

## Business Entities

- **Import Collection Variables Dialog**: The primary dialog interface allowing users to browse and import variables from workspace or remote collections.
- **Catalog Discovery**: The asynchronous background operation responsible for enumerating remote connections and listing available library collections.
- **Discovery Feedback & Retry**: The user-facing status indicator and retry action representing the health and state of background catalog discovery.
- **Lifecycle Generation**: The tracking identifier used to match asynchronous discovery results with the active dialog request, ensuring stale responses are discarded.
- **Workspace Collection**: Local collections residing in the user's active workspace that must remain usable regardless of remote discovery state.
- **Remote Library Collection**: Collections retrieved from configured external library connections.

## Q&A

- **Q: Why is automated coverage for discovery failure and retry critical?**
  **A:** Background asynchronous discovery communicates with external services over networks that can be slow, intermittent, or misconfigured. Automated verification ensures the user experience remains reliable and resilient during failures, preventing regressions where errors crash the UI, block local collections, or leak background worker threads.
- **Q: How does retry interact with existing local collections?**
  **A:** Local workspace collections are populated immediately and remain intact. Retrying discovery solely targets remote library catalog enumeration and must never wipe, lock, or invalidate workspace collection selections.
- **Q: What programming language is used for implementation?**
  **A:** Python.