# PYPOST-1217: Stabilize test_live_collection_tree_missing_option_raises under parallel make test

## Goals

This task delivers the stabilization of `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises`
under parallel test execution (`make test`), building upon the empirical evidence baseline established
in [PYPOST-1215](https://pypost.atlassian.net/browse/PYPOST-1215) (REPRO-1) and the root-cause diagnosis
delivered in [PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216) (DIAG-1).

From a business, engineering, and testing reliability perspective:
- **CI Gate Stability**: The parallel test suite (`make test`) serves as the primary automated
  regression gate across developer workstations and CI runners. Flaky test failures block pull
  requests, increase build cycle latency, erode engineer trust in CI signals, and demand manual
  reruns. Eliminating this flake makes the parallel test gate completely reliable.
- **Preventing Test Suite Timeouts & Stalls**: Under multi-worker parallel execution, scheduling
  contention can cause test nodes to inflate in duration, risking worker-level timeouts (120s) or
  test timeouts (60s) that abort the entire suite. Stabilizing the test node ensures predictable,
  bounded execution times.
- **Preserving Test Contract Fidelity**: The negative interaction assertion contract established
  in [PYPOST-975](https://pypost.atlassian.net/browse/PYPOST-975) guarantees that invalid user actions
  against the collection tree raise appropriate domain errors (`UiTargetNotInteractableError`
  with `"option not found"`). Stabilization must preserve this behavioral invariant without softening,
  diluting, or deleting assertions.
- **Explicit Scope Boundaries**: Ensuring the stabilization remains strictly focused on this
  compound contention failure mode without conflating or silently merging with prior-art GUI
  issues ([PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117) large-batch segfault or
  [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115) /
  [PYPOST-1040](https://pypost.atlassian.net/browse/PYPOST-1040) dialog GC teardown).

## Programming Language

- **Implementation Language**: Python (for test stabilization, test harness synchronization,
  and verification)
- **Documentation**: English Markdown (for task artifacts and dev docs updates)

## User Stories

- As a **PyPost Developer**, I want `make test` and `make check` to execute reliably and pass
  consistently on my local machine and in CI without intermittent failures in
  `test_live_collection_tree_missing_option_raises`, so that I can rapidly iterate and merge
  features with confidence in automated test results.
- As a **CI Engineer**, I want the parallel test runner to complete across all parallel subprocess
  workers without thread stalls, worker timeout kills, or flaky test node failures, so that CI
  pipeline throughput remains fast, predictable, and cost-effective.
- As a **Test Maintainer**, I want the negative interaction contract for `COLLECTION_TREE` to be
  strictly enforced and verified without speculative delays or relaxed assertions, so that real
  UI interactability bugs in the collection tree are never missed.

## Definition of Done

This task is considered `done` when all of the following acceptance criteria are met:

1. **Test Stability Under Parallel Execution**:
   The named test node `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises`
   executes with a 100% pass rate under parallel test execution (`make test`), with flake eliminated
   across repeated runs. If any residual concurrency risk remains, it is explicitly documented with
   an identified owner and follow-up ticket.
2. **Preservation of Negative Assertion Contract**:
   The negative interaction assertion contract from
   [PYPOST-975](https://pypost.atlassian.net/browse/PYPOST-975) remains strictly intact: selecting
   an absent option from `COLLECTION_TREE` raises `UiTargetNotInteractableError` containing
   `"option not found"`. No assertion is weakened, bypassed, or removed unless an explicit, reviewed
   acceptance criteria change documents otherwise.
3. **Empirical Validation Against REPRO-1 Procedure**:
   The fix is validated against the differential execution procedures established in REPRO-1
   (`ai-tasks/PYPOST-1215/baseline-evidence.md`), confirming 100% pass rates across:
   - Isolated single-node profile (`tests/test_ui_actions.py -k test_live_collection_tree_missing_option_raises`).
   - Isolated single-file profile (`tests/test_ui_actions.py`).
   - Concurrent subset profile (multi-worker run of UI, Agent, and MCP suites).
   - Full repository parallel suite (`make test`).
4. **Architectural Boundary & No Silent Merge**:
   The fix strictly addresses this specific failure mode (Class 2 compound GIL/CPU contention and
   event loop starvation). No silent merge into [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117)
   or [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115) /
   [PYPOST-1040](https://pypost.atlassian.net/browse/PYPOST-1040) is permitted; cross-links stay
   explicit if a shared cause is referenced.
5. **Make-Only Tooling Gate Compliance**:
   All verification operations conform to repository standards (`AGENTS.md`), executing exclusively
   through Make targets (`make lint`, `make test`, `make verify-ai-tasks`, and `make check`).
6. **Top-Down Artifacts & Documentation**:
   All required workflow artifacts in `ai-tasks/PYPOST-1217/` are produced, verified, and developer
   documentation in `doc/dev/` is updated to record stabilization conclusions.

## Task Description

### Problem Statement

In [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167) Step 4 development, an intermittent
failure was discovered in `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises`
under parallel test execution (`make test`), while isolated test runs passed cleanly.

Under parent epic [PYPOST-1188](https://pypost.atlassian.net/browse/PYPOST-1188), this issue was
decomposed into three sequential child stories:
1. **REPRO-1 ([PYPOST-1215](https://pypost.atlassian.net/browse/PYPOST-1215))**: Captured the empirical
   baseline and differential execution profiles (`ai-tasks/PYPOST-1215/baseline-evidence.md`), showing
   that the test node is 100% reliable in isolation (~1.37s) but experiences +40.3% timing inflation
   and intermittent timeouts under full multi-worker parallel execution (8 workers on 6 CPU cores).
2. **DIAG-1 ([PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216))**: Diagnosed the root cause
   (`ai-tasks/PYPOST-1216/30-diagnosis-report.md`), empirically refuting the suspected in-memory race
   between Qt `apply_theme` and background `uvicorn` imports/servers, and confirming the failure as
   Class 2: compound GIL/CPU contention and Qt event loop pump starvation delaying signal dispatch
   and UI readiness settling.
3. **FIX-1 ([PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217))**: *This task* — delivers
   the stabilization implementation, ensuring deterministic event settlement, eliminating the flake,
   and verifying the fix across the parallel test gate.

### Scope & System Boundaries

#### In-Scope
- Stabilizing the execution of `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises`
  under multi-worker parallel test execution (`make test`).
- Ensuring that session startup and UI event loop polling settle deterministically before widget
  interaction occurs.
- Validating the stabilization against the empirical REPRO-1 profiles across multiple repeated runs.
- Preserving the exact negative assertion contract (`UiTargetNotInteractableError` with `"option not found"`).
- Providing complete observability and logging for event loop settlement and test lifecycle events.
- Updating developer-facing testing documentation in `doc/dev/` to reflect stabilization insights.

#### Out-of-Scope (Non-Goals)
- **Do Not Re-Open Baselines**: Do not reopen or relitigate the REPRO-1 evidence baseline or the
  DIAG-1 root-cause findings. The exact technical and architectural design of the fix is owned
  by Step 2 Architecture of this story.
- **No Implementation Details in Requirements**: In accordance with the Top-Down workflow standard,
  this document describes *what* must be achieved from a functional and business perspective, not
  *how* the code will be structured.
- **No Assertion Dilution**: Do not soften, skip, or remove the negative interaction assertions.
  Do not introduce arbitrary sleep statements into test bodies.
- **No Silent Merge with Prior Art**: Do not merge this story into [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117)
  (large-batch segfault) or [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115) /
  [PYPOST-1040](https://pypost.atlassian.net/browse/PYPOST-1040) (dialog GC teardown). Cross-references
  must remain explicit.
- **No Scope Expansion to Unrelated Tests**: Focus stabilization specifically on the named node and its
  direct lifecycle dependencies; do not attempt broad rewrites of unrelated test modules.

### Functional Requirements

- **FR1 (Parallel Execution Stability)**: The target test node must run deterministically and pass
  without timeouts or failures when executed concurrently alongside the rest of the test suite under
  `make test` (across default multi-worker pools, e.g., 8 workers).
- **FR2 (Negative Assertion Preservation)**: The test must strictly verify that attempting to select
  a missing item (`"__no_such_collection_tree_option__"`) in `COLLECTION_TREE` raises
  `UiTargetNotInteractableError` with an error message containing `"option not found"`.
- **FR3 (Readiness Synchronization)**: The test execution lifecycle must ensure that all required UI
  initialization, model loading, and queued layout/styling events have settled before widget interactions
  are executed, preventing race conditions caused by CPU scheduling jitter.
- **FR4 (Differential Verification)**: The stabilization must be validated across the four REPRO-1
  profiles (isolated node, isolated file, concurrent subset, and full repository parallel suite),
  demonstrating zero failures.
- **FR5 (Observability & Diagnostics)**: Test startup and UI wait settlement must emit structured
  diagnostic telemetry to facilitate debugging and ensure that any unexpected timeout yields
  informative error context.

### Non-Functional Requirements

- **NFR1 (Performance & Efficiency)**: Stabilization must not introduce unnecessary latency or
  unbounded delays. The execution time of `tests/test_ui_actions.py` must remain fast and well within
  the 60-second test timeout and 120-second worker timeout limits.
- **NFR2 (Tooling Standard Compliance)**: All operations (testing, linting, verification) must strictly
  use `make` targets (`make test`, `make lint`, `make verify-ai-tasks`, `make check`), adhering to
  `AGENTS.md`. No raw CLI tools (`pytest`, `flake8`, `mypy`) may be invoked directly.
- **NFR3 (Deterministic Quality Gate)**: Full repository quality gates (`make check`) must pass cleanly
  with zero lint errors, zero test failures, and valid workflow task artifacts.
- **NFR4 (Traceability & Base Commit Anchor)**: All changes and empirical measurements must be anchored
  to the baseline established in commit `353370cdbd19c7a3338e2ed05c292b0a404d7b90`.

### Constraints and Assumptions

- **Empirical Continuity**: This work assumes the validity of REPRO-1 (`ai-tasks/PYPOST-1215/baseline-evidence.md`)
  and DIAG-1 (`ai-tasks/PYPOST-1216/30-diagnosis-report.md`).
- **Make-Only Enforcement**: Direct execution of Python test scripts or CLI tools outside Makefile
  targets is strictly prohibited.
- **Single Contention Class**: The flake is caused by Class 2 compound GIL/CPU contention and Qt event
  pump starvation under multi-worker parallel execution, rather than an in-memory thread safety bug
  or C++ native leak.

### Main Entities (Business & Testing Perspective)

| Entity | Role / Description |
| --- | --- |
| **Target Test Node** | `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises`, the specific negative interaction test being stabilized. |
| **Negative Assertion Contract** | The invariant established in PYPOST-975 requiring `UiTargetNotInteractableError` with `"option not found"`. |
| **Parallel Quality Gate** | The `make test` and `make check` suites running across multiple concurrent subprocess workers. |
| **Session Readiness State** | The state where the application window, collection tree model, and queued event loop events have completely settled. |
| **Timeout Hierarchy** | The multi-tiered bounds protecting test execution (60s test timeout, 120s worker timeout, 10s/30s UI wait limits). |
| **REPRO-1 Profiles** | The four standard verification configurations: isolated node, isolated file, concurrent subset, and full parallel suite. |

## Q&A

- **Q: What is the primary business reason for this task?**
  - **A:** The primary business reason is to restore 100% reliability to the parallel test gate
    (`make test`), eliminating intermittent CI failures and stalls that disrupt engineering velocity
    and delay software delivery.
- **Q: Why are technical and architectural details omitted from this document?**
  - **A:** In accordance with the Top-Down workflow standard (`td-10-requirements`), Step 1 focuses
    exclusively on *what* must be achieved from a functional, business, and testing perspective.
    Specific technical mechanisms, synchronization designs, and code changes are reserved for
    Step 2 (Architecture) and Step 4 (Development).
- **Q: Does this task re-investigate the root cause?**
  - **A:** No. Root-cause analysis was completed and verified in DIAG-1
    ([PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216)). This task focuses strictly on
    designing, implementing, and validating the stabilization fix based on those diagnostic findings.
- **Q: Can we resolve the flake by simply increasing timeouts or adding arbitrary sleep calls?**
  - **A:** No. Ad-hoc sleeps and arbitrary timeout inflations mask underlying synchronization flaws,
    slow down the test suite, and fail to guarantee determinism under heavy CPU load. Stabilization
    must ensure deterministic event settlement.
- **Q: Can the negative assertion contract be modified if it makes the test pass?**
  - **A:** No. Preserving the exact negative assertion (`UiTargetNotInteractableError` containing
    `"option not found"`) is a mandatory acceptance criterion. Changing this contract would compromise
    test coverage for user error handling in the collection tree.

## References

- [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217) — This stabilization story (FIX-1)
- [PYPOST-1188](https://pypost.atlassian.net/browse/PYPOST-1188) — Parent epic (Stabilize `test_live_collection_tree_missing_option_raises`)
- [PYPOST-1215](https://pypost.atlassian.net/browse/PYPOST-1215) — Upstream REPRO-1 baseline evidence (`ai-tasks/PYPOST-1215/baseline-evidence.md`)
- [PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216) — Upstream DIAG-1 root-cause diagnosis (`ai-tasks/PYPOST-1216/30-diagnosis-report.md`)
- [PYPOST-1205](https://pypost.atlassian.net/browse/PYPOST-1205) — Epic decomposition story (`ai-tasks/PYPOST-1205/10-requirements.md`)
- [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167) — Discovery task note (`ai-tasks/PYPOST-1167/60-tech-debt.md` item 6)
- [PYPOST-975](https://pypost.atlassian.net/browse/PYPOST-975) — Originating task for `COLLECTION_TREE` negative selection assertions
- [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117) — Excluded prior art epic (large-batch segfault)
- [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115) / [PYPOST-1040](https://pypost.atlassian.net/browse/PYPOST-1040) — Excluded prior art epics (SettingsDialog GC teardown)
- `tests/test_ui_actions.py` — Location of target test node
- `doc/dev/testing.md` — Testing guidelines and parallel execution documentation
