# PYPOST-1182: Unhang tests/test_collections_import_ui.py Qt wait in make test

## Goals

During development and continuous integration runs (such as observed in [PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157)), the test suite execution can become indefinitely hung or stalled on `tests/test_collections_import_ui.py` due to unhandled GUI / event wait states. This causes full-suite test runs and isolated test executions to exceed timeouts, waste CI resources, block developer feedback loops, and require manual process termination.

The goal of this task is to ensure that all automated tests in `tests/test_collections_import_ui.py` run to completion deterministically, reliably, and within reasonable time bounds during test execution (`make test`), without skipping, xfailing, or removing any of the existing test coverage.

## User Stories

- As a **developer / maintainer**, I want `make test` and isolated test executions of `tests/test_collections_import_ui.py` to reliably complete without hanging or deadlocking, so that I receive fast, predictable feedback on my changes.
- As a **CI / QA engineer**, I want all automated test cases in `tests/test_collections_import_ui.py` to remain fully active and enforced (not skipped, xfailed, or deleted), so that collection import functionality is thoroughly verified against regressions.
- As a **test runner / framework operator**, I want test event loops and background operations to properly bound their wait times and terminate cleanly, so that subsequent test runs are not blocked or corrupted.

## Definition of Done

This task is considered done when:

1. Running `make test` or `make test PYTEST_ARGS='tests/test_collections_import_ui.py'` completes deterministically and passes without hanging or stalling.
2. Isolated and parallel test executions of `tests/test_collections_import_ui.py` consistently finish well within their declared pytest timeout limits.
3. Zero test degradation: no test cases in `tests/test_collections_import_ui.py` are disabled, skipped, xfailed, or removed.
4. All existing collection import scenarios and assertions (entry point identification, happy path import, conflict resolution, parse error handling, storage failure recovery, and event logging) continue to be fully verified.
5. All Top-Down workflow artifacts for PYPOST-1182 are created and maintained per project guidelines.

## Task Description

### Programming Language

Python — pytest suite and PyPost desktop client components.

### Problem

Full-suite test runs (`make test`) and isolated invocations of `tests/test_collections_import_ui.py` can hang for extended periods (e.g. 10+ minutes) in Qt wait states without tests completing. Standard timeout guards fail to cleanly terminate the stalled test executions, resulting in hung test worker processes and interrupted CI pipelines.

### Business Need

Automated testing is the primary quality gate for PyPost. When test suites hang unpredictably:
- Developer productivity is significantly impaired by stalled local test runs.
- CI pipeline capacity is wasted on deadlocked test workers.
- Flaky or hung tests undermine confidence in automated regression testing.

Resolving the hang while preserving all collection import test cases ensures high test suite reliability and robust quality assurance.

### Scope

#### In Scope

- Ensuring that all test cases in `tests/test_collections_import_ui.py` execute and terminate cleanly without hanging or exceeding time limits.
- Ensuring event processing and wait mechanisms in collection import UI tests reliably observe timeout and completion conditions.
- Preserving 100% of existing collection import test coverage and assertions.
- Maintaining test execution compatibility with both isolated and parallel multi-worker `make test` runs.

#### Out of Scope

- Changing user-visible collection import features, business rules, or user interface dialogs.
- Modifying collection import file format parsers or conflict resolution algorithms.
- Disabling, skipping, xfailing, or deleting any test cases in `tests/test_collections_import_ui.py`.
- Fixing unrelated flaky tests or issues in other test modules (e.g. PYPOST-1181, PYPOST-1178).

### Main Entities (Business Perspective)

| Entity | Role |
| --- | --- |
| **Collection Import Test Suite** | Automated test suite verifying user import of collections and requests into PyPost. |
| **Test Execution Gate** | The `make test` quality gate that validates code correctness across parallel test workers. |
| **Wait / Completion Guard** | Mechanism that synchronizes asynchronous test actions with test assertions within bounded deadlines. |
| **Collection Import Actions** | Business workflow for selecting, parsing, resolving conflicts, and persisting imported collections. |

### Functional Requirements

| ID | Requirement |
| --- | --- |
| **FR-1** | All test cases in `tests/test_collections_import_ui.py` must execute to completion and pass deterministically when invoked via `make test`. |
| **FR-2** | Isolated execution via `make test PYTEST_ARGS='tests/test_collections_import_ui.py'` must complete without hanging or stalling. |
| **FR-3** | All existing test coverage in `tests/test_collections_import_ui.py` must be preserved: entry points, tree refresh, conflict prompts (overwrite, skip, keep both, apply to all), invalid files, storage failures, and telemetry logging. |
| **FR-4** | Asynchronous operations and wait conditions within the test suite must reliably yield and finish when conditions are met or when deadlines expire. |

### Non-Functional Requirements

- **NFR-1 (Reliability):** Test execution must be deterministic and free of race conditions or deadlocks across repeated test runs.
- **NFR-2 (Performance):** Test execution of `tests/test_collections_import_ui.py` must complete promptly (well within module timeouts) to maintain fast test suite throughput.
- **NFR-3 (Test Integrity):** No test skipping, xfailing, or deletion is permitted.
- **NFR-4 (Tooling Standard):** All test and quality gate executions must strictly use `make` targets (`make test`, `make check`).

### Constraints and Assumptions

- Source task: Follow-up 2 from `ai-tasks/PYPOST-1157/60-tech-debt.md`.
- Base commit: `1cc642b2ef7ff554228a5022cc5de866be6e72fb`.
- Operating environment: Linux with headless Qt (offscreen platform).
- All tests declare module-level `pytestmark = pytest.mark.timeout(...)`.

## Q&A

- **Why is this task needed if tests sometimes pass quickly?**
  Intermittent or pre-existing hangs in test suites can stall CI pipelines and parallel test runners unpredictably. Deterministic completion is necessary for stable quality gates.
- **Can we resolve the hang by skipping or xfailing slow tests?**
  No. Project rules and the Jira ticket explicitly prohibit skipping, xfailing, or deleting any test cases in `tests/test_collections_import_ui.py`.
- **Does this change any product features for collection import?**
  No. The business rules, file format support, conflict options, and user workflows for collection import remain unchanged.

## References

- Jira ticket: [PYPOST-1182](https://pypost.atlassian.net/browse/PYPOST-1182)
- Discovered in: [PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157) (`ai-tasks/PYPOST-1157/60-tech-debt.md`)
- Test module: `tests/test_collections_import_ui.py`
- Operating guidelines: [AGENTS.md](file:///home/src/AGENTS.md)
