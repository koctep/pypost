# PYPOST-1215: Owned parallel flake evidence for test_live_collection_tree_missing_option_raises

## Goals

This task establishes an owned, documented, and repeatable empirical baseline of the intermittent failure of `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises` under parallel test execution (`make test`), contrasting it with its reliable passing behavior in isolated execution.

From a business and engineering perspective:
- **CI Reliability & Trust**: Flaky test failures in parallel test suites degrade developer confidence, slow down pull request merges, and obscure genuine regression failures.
- **Empirical Baseline for Downstream Slices**: Serves as the foundation for child tasks [PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216) (DIAG-1: root-cause diagnosis) and [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217) (FIX-1: stabilization) by eliminating ambiguity and tribal knowledge regarding how the flake manifests.
- **Preservation of Behavioral Locks**: Ensures that evidence collection focuses on the actual test condition (verifying that a missing option in `COLLECTION_TREE` raises `UiTargetNotInteractableError` with `"option not found"`, introduced in PYPOST-975) without masking or diluting the assertion.

## Programming Language

- **Implementation Language**: Python (for test execution, repro procedure, and harness validation)
- **Documentation**: English Markdown (for evidence recording, baseline reports, and developer documentation)

## User Stories

- As a **CI Engineer / Test Maintainer**, I want a documented, repeatable procedure that consistently reproduces the parallel suite flake and demonstrates isolated-file pass, so that test instability is deterministically verifiable instead of relying on anecdotal reports.
- As a **Root Cause Investigator (DIAG-1 / PYPOST-1216 implementer)**, I want a concrete evidence baseline recording the environment, command shape, base commit reference (`353370cd…`), and exact failure mode/trace, so that I can diagnose the underlying interaction mechanism without re-discovering how to trigger the failure.
- As a **Fix/Stabilization Engineer (FIX-1 / PYPOST-1217 implementer)**, I want clear benchmark criteria contrasting parallel execution failure with isolated success, so that I can later verify that the fix eliminates the flake under equivalent parallel load without weakening the intended negative assertion.
- As a **PyPost Maintainer**, I want this flake investigation kept distinctly scoped from related GUI issues (such as PYPOST-1117 large-batch segfault or PYPOST-1115 GC teardown) unless empirical evidence proves a shared root cause, so that investigation efforts remain focused.

## Definition of Done

This task is considered `done` when:

1. **Documented, Repeatable Repro Procedure**: A clear, repeatable procedure is defined and documented that reproduces the intermittent failure of `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises` under parallel execution (`make test` or justified equivalent load) and contrasts with an isolated-file/node pass.
2. **Empirical Baseline Evidence**: Baseline evidence is captured and recorded, containing:
   - Execution environment details (Python runtime, OS, Qt platform plugin configuration).
   - Exact command shapes used for parallel execution vs isolated execution.
   - Base commit reference `353370cdbd19c7a3338e2ed05c292b0a404d7b90` (HEAD prior to PYPOST-1167).
   - Observed failure mode, error symptoms, output logs, or stack traces.
3. **Downstream Handoff Readiness**: The baseline documentation and repro procedure are sufficiently detailed and self-contained for [PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216) (DIAG-1) and [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217) (FIX-1) to cite and execute directly without re-deriving findings from PYPOST-1167 notes.
4. **Scope Integrity**: Non-goals are strictly respected: no root-cause diagnosis, no code stabilization/fixes, and no merging into PYPOST-1117/1115.
5. **Top-Down Artifacts**: `ai-tasks/PYPOST-1215/00-roadmap.md` and `ai-tasks/PYPOST-1215/10-requirements.md` exist and comply with repository standards.

## Task Description

### Problem Statement

During parallel test runs (`make test`), the test node `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises` exhibits intermittent failures/hangs, whereas running the test node or its file in isolation consistently passes. This test locks the negative behavior for UI select interactions on the live `COLLECTION_TREE` widget (expecting `UiTargetNotInteractableError` with `"option not found"`).

Because this failure was observed during unrelated feature development (PYPOST-1167), it was logged as technical debt (item 6) and promoted to Epic [PYPOST-1188](https://pypost.atlassian.net/browse/PYPOST-1188). In [PYPOST-1205](https://pypost.atlassian.net/browse/PYPOST-1205), PYPOST-1188 was decomposed into three sequential child stories:
1. **REPRO-1 ([PYPOST-1215](https://pypost.atlassian.net/browse/PYPOST-1215))**: Owned parallel flake evidence and baseline (*this task*).
2. **DIAG-1 ([PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216))**: Root-cause diagnosis.
3. **FIX-1 ([PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217))**: Stabilization under parallel `make test`.

### Scope & System Boundaries

#### In Scope
- Defining a repeatable execution procedure to reproduce the intermittent parallel failure of `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises`.
- Defining a contrasting procedure to demonstrate reliable passing execution of the test in isolation.
- Capturing and documenting structured baseline evidence (environment, invocation commands, base commit reference `353370cdbd19c7a3338e2ed05c292b0a404d7b90`, observed failure mode, logs).
- Formatting artifacts for direct consumption and citation by DIAG-1 (PYPOST-1216) and FIX-1 (PYPOST-1217).

#### Out of Scope (Non-Goals)
- **No Root-Cause Diagnosis**: Determining whether the issue stems from a Qt `apply_theme` vs uvicorn import race, event loop contention, fixture teardown timing, or another mechanism is deferred to DIAG-1 (PYPOST-1216).
- **No Production or Test Stabilization**: Modifying production code or changing test assertions/fixture lifecycle to fix the flake is deferred to FIX-1 (PYPOST-1217).
- **No Scope Merging**: Do not merge this task into PYPOST-1117 (large-batch `apply_theme` segfault) or PYPOST-1115 (QWidgetItem GC teardown).
- **No Assertion Dilution**: Do not alter or weaken the expected `UiTargetNotInteractableError` / `"option not found"` lock.
- **No Architecture in Step 1**: Technical design of the repro harness/scripting is deferred to Step 2.

### Functional Requirements

- **FR1 (Reproduction Procedure)**: The system/procedure must specify a documented, executable mechanism to trigger and observe the parallel flake under multi-worker/parallel test conditions.
- **FR2 (Contrast Procedure)**: The system/procedure must specify an executable mechanism to demonstrate that the test node passes when run in isolation (single node or single file execution).
- **FR3 (Baseline Evidence Capture)**: The baseline record must include:
  - Base commit hash: `353370cdbd19c7a3338e2ed05c292b0a404d7b90`.
  - Execution environment details (OS, Python version, PySide6/Qt platform parameters).
  - Exact command lines / invocation shapes.
  - Observed failure mode (exception message, traceback, hang/timeout, or exit status).
  - Pass/fail run statistics (e.g., failure frequency under load vs 100% pass in isolation).
- **FR4 (Downstream Handoff)**: Baseline artifacts must be organized and stored in `ai-tasks/PYPOST-1215/` so that subsequent tasks (PYPOST-1216 and PYPOST-1217) can cite them without relying on chat transcripts or PYPOST-1167 scratch notes.

### Non-Functional Requirements

- **NFR-1 (Repeatability)**: The reproduction procedure must provide high reproducibility under the specified load/parallel conditions.
- **NFR-2 (Integrity & Safety)**: The repro procedure must not leave side-effects, orphaned background processes, or modified workspace files that corrupt the repository state.
- **NFR-3 (Traceability)**: All findings must explicitly reference the base commit `353370cdbd19c7a3338e2ed05c292b0a404d7b90`, parent epic [PYPOST-1188](https://pypost.atlassian.net/browse/PYPOST-1188), and source [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167).
- **NFR-4 (Tooling Standard)**: All test and check executions must conform to the repository's Make-only standard (`make ...`).

### Constraints and Assumptions

- **Base Commit Baseline**: Primary reference point is commit `353370cdbd19c7a3338e2ed05c292b0a404d7b90` (HEAD before PYPOST-1167 changes).
- **Make-Only Enforcement**: Direct invocation of raw CLI tools (`pytest`, `flake8`, `pip`) is prohibited per `AGENTS.md`. All runs must go through `make` targets or Make-backed harnesses.
- **Intermittent Nature**: As a concurrency/load race condition, reproduction may require multiple iterations or specific parallel worker configurations to manifest.
- **Independence from Unrelated Epics**: The issue is treated as distinct from PYPOST-1117 and PYPOST-1115 unless downstream diagnosis in DIAG-1 proves common causality.

### Main Entities (Business Perspective)

| Entity | Role / Description |
| --- | --- |
| **Flaky Target Node** | `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises`, verifying negative `ui_select` error raising. |
| **Parallel Test Execution** | Multi-process/parallel suite run (`make test` load) under which the flake manifests. |
| **Isolated Test Execution** | Single-file or single-node test run demonstrating expected passing behavior. |
| **Baseline Evidence Record** | Documented dataset capturing environment, commands, commit baseline, failure symptoms, and contrast results. |
| **Downstream Tasks** | [PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216) (DIAG-1) and [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217) (FIX-1), which rely on this baseline. |

## Q&A

- **Q: Why is evidence collection separated into its own task instead of diagnosing and fixing immediately?**
  - **A:** Decomposing oversized epics into distinct slices (REPRO-1 -> DIAG-1 -> FIX-1) ensures that each task stays within the manageable <=5 SP limit, prevents speculative fixes on unconfirmed behavior, and creates an objective benchmark against which fixes can be validated.
- **Q: Does this task modify production code in `pypost/` or test assertions in `tests/`?**
  - **A:** No. This task produces only reproduction procedures, empirical baseline evidence, and documentation. No production logic or test assertion logic is changed.
- **Q: Why must base commit `353370cdbd19c7a3338e2ed05c292b0a404d7b90` be documented?**
  - **A:** This commit represents the repository state where the flake was first observed during PYPOST-1167, ensuring that evidence is anchored to a known baseline and independent of subsequent modifications.
- **Q: Does this task determine why the test flakes (e.g., verifying the Qt/uvicorn hypothesis)?**
  - **A:** No. Formulating and confirming the root-cause hypothesis is the explicit responsibility of DIAG-1 ([PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216)).
- **Q: Is a red automated test required for Step 3 of PYPOST-1215?**
  - **A:** In this repro-baseline task, Step 3 will record the red/flaking execution behavior of the target node under parallel load (or document appropriate N/A status depending on architecture determination), while preserving the passing contrast in isolation.

## References

- [PYPOST-1215](https://pypost.atlassian.net/browse/PYPOST-1215) — This story (REPRO-1)
- [PYPOST-1188](https://pypost.atlassian.net/browse/PYPOST-1188) — Parent epic (Stabilize `test_live_collection_tree_missing_option_raises`)
- [PYPOST-1205](https://pypost.atlassian.net/browse/PYPOST-1205) — Epic decomposition story
- [PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216) — Downstream diagnosis story (DIAG-1)
- [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217) — Downstream fix story (FIX-1)
- [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167) — Discovery context (`ai-tasks/PYPOST-1167/60-tech-debt.md` item 6)
- [PYPOST-975](https://pypost.atlassian.net/browse/PYPOST-975) — Originating task for `COLLECTION_TREE` negative selection assertions
- [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117) — Excluded prior art epic (large-batch `apply_theme` segfault)
- [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115) — Excluded prior art epic (SettingsDialog/QWidgetItem GC teardown)
- `tests/test_ui_actions.py` — Location of `test_live_collection_tree_missing_option_raises`
- `doc/dev/testing.md` — Testing documentation and negative selection test descriptions
