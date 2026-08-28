# PYPOST-1216: Root-cause diagnosis of apply_theme vs uvicorn race for collection-tree flake

## Goals

This task delivers a definitive, evidence-backed root-cause diagnosis of the intermittent failure affecting `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises` under parallel test suite execution (`make test`), building directly upon the empirical baseline established in [PYPOST-1215](https://pypost.atlassian.net/browse/PYPOST-1215) (REPRO-1).

From a business, engineering, and architectural perspective:
- **CI Reliability & Root-Cause Clarity**: Flaky tests in the core parallel test gate erode developer confidence and slow delivery cycles. Resolving test instability requires identifying the exact underlying mechanism rather than relying on unverified hypotheses or applying speculative, masking workarounds.
- **Hypothesis Resolution**: Formally confirms, refutes, or replaces the initial suspicion recorded during [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167) that a race between Qt `apply_theme` stylesheet parsing and background `uvicorn` imports/servers causes the flake.
- **Architectural Boundary & Scope Separation**: Explicitly differentiates this failure mode from related prior-art GUI issues—specifically [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117) (large-batch `apply_theme` native segfault) and [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115) / [PYPOST-1040](https://pypost.atlassian.net/browse/PYPOST-1040) (`SettingsDialog`/`QWidgetItem` garbage collection teardown)—ensuring that future stabilization efforts operate at the proper subsystem boundary without conflating distinct failure classes.
- **Actionable Stabilization Handoff**: Provides a solid, unambiguous diagnostic foundation for [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217) (FIX-1) so that the stabilization implementation can proceed directly to fix design and validation without needing to reopen the failure class question.
- **Preservation of Behavioral Invariants**: Ensures that diagnosis respects the negative interaction assertion contract established in [PYPOST-975](https://pypost.atlassian.net/browse/PYPOST-975) (verifying that selecting an absent item in `COLLECTION_TREE` raises `UiTargetNotInteractableError` containing `"option not found"`).

## Programming Language

- **Implementation Language**: Python (for diagnostic probes, trace instrumentation, profiling, and verification scripts)
- **Documentation**: English Markdown (for root-cause analysis documentation, comparative matrices, and developer guidance)

## User Stories

- As a **PyPost Maintainer & CI Owner**, I want an evidence-backed root-cause diagnosis of the collection-tree flake under parallel test execution, so that CI stability investments target the actual contention mechanism rather than unverified assumptions.
- As a **Stabilization Engineer (FIX-1 / PYPOST-1217 implementer)**, I want a conclusive determination of the failure class (confirming, refuting, or replacing the suspected `apply_theme` vs `uvicorn` race) along with clear constraints and architectural findings, so that I can implement targeted stabilization without having to re-investigate root cause.
- As a **Test Architect**, I want an explicit distinction between this flake and related prior art (such as PYPOST-1117 large-batch segfault and PYPOST-1115 GC teardown), so that test isolation, fixture lifecycles, and event loop handling are addressed at the correct system layer.
- As a **Developer / Contributor**, I want developer-facing documentation explaining the interaction between Qt GUI sessions, background server threads, and multi-worker subprocess scheduling, so that future test authors do not reintroduce similar concurrency races.

## Definition of Done

This task is considered `done` when:

1. **Written Diagnosis with Evidence-Backed Failure Class**: A formal root-cause diagnosis document is produced that conclusively confirms, refutes, or replaces the suspected Qt `apply_theme` vs `uvicorn` race based on empirical diagnostic probes, profiling data, or execution traces.
2. **Explicit Distinction from Related Prior Art**: The diagnosis explicitly contrasts and distinguishes this flake mechanism from:
   - [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117) (large-batch `apply_theme` native segfault under ~110-module GUI batch execution).
   - [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115) / [PYPOST-1040](https://pypost.atlassian.net/browse/PYPOST-1040) (`SettingsDialog` / `QWidgetItem` GC teardown during dialog destruction).
   The document details specific differences in failure symptoms, triggering conditions, and lifecycle phases.
3. **Actionable Downstream Handoff for FIX-1**: Diagnostic findings and constraints are sufficiently specific for [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217) (FIX-1) to select and implement an effective stabilization approach without reopening investigation into the failure class.
4. **Developer-Facing Documentation**: Dev-facing notes record the conclusions, mechanisms, and architectural implications for maintainers in `doc/dev/`.
5. **Scope Integrity & Non-Goals**: No production or test code stabilization fix is implemented in this task (deferred to FIX-1); no silent merging of scopes into PYPOST-1117 or PYPOST-1115.
6. **Top-Down Artifacts**: `ai-tasks/PYPOST-1216/00-roadmap.md` and `ai-tasks/PYPOST-1216/10-requirements.md` exist and conform to repository standards.

## Task Description

### Problem Statement

During parallel test execution (`make test`), the test node `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises` intermittently fails or hangs. In isolated single-node or single-file runs, the test passes deterministically (as verified by the REPRO-1 baseline in `ai-tasks/PYPOST-1215/baseline-evidence.md`).

This flake was first observed during [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167) Step 4 development, where a suspicion arose that a race condition existed between Qt `apply_theme` stylesheet processing and background `uvicorn` import/server lifecycles under parallel test load. In [PYPOST-1205](https://pypost.atlassian.net/browse/PYPOST-1205), Epic [PYPOST-1188](https://pypost.atlassian.net/browse/PYPOST-1188) was decomposed into three sequential units:
1. **REPRO-1 ([PYPOST-1215](https://pypost.atlassian.net/browse/PYPOST-1215))**: Owned parallel flake evidence and baseline (*completed*).
2. **DIAG-1 ([PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216))**: Root-cause diagnosis (*this task*).
3. **FIX-1 ([PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217))**: Stabilization under parallel `make test`.

This story (DIAG-1) executes the investigative step: analyzing the exact execution path of `test_live_collection_tree_missing_option_raises`, instrumenting diagnostic probes, evaluating candidate hypotheses (Qt event loop pump, stylesheet application, uvicorn server startup/import, subprocess worker contention), and delivering an empirical determination of the failure class.

### Scope & System Boundaries

#### In Scope
- Investigating the execution path and runtime behavior of `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises` under multi-worker parallel execution.
- Evaluating the `apply_theme` vs `uvicorn` race hypothesis against alternative contention mechanisms (e.g., Qt event loop polling latency in `AgentAppSession.window.is_ui_ready`, socket/server thread contention, offscreen QPA rendering delays).
- Producing a written diagnostic report detailing the confirmed failure class with supporting trace/profiling evidence.
- Providing an explicit comparison matrix distinguishing this failure mode from PYPOST-1117 and PYPOST-1115/1040.
- Defining precise technical recommendations and constraints for FIX-1 ([PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217)).
- Recording findings in maintainer-facing developer documentation.

#### Out of Scope (Non-Goals)
- **No Stabilization Fix (FIX-1)**: Do not modify production code (`pypost/`) or apply test stabilization logic/harness changes to resolve the flake; that work is exclusively allocated to [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217).
- **No Silent Merging**: Do not merge this issue into [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117) or [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115). If a shared underlying cause is uncovered, document the relationship explicitly via cross-links rather than consolidating scopes.
- **No Assertion Alteration**: Do not alter, weaken, or bypass the `UiTargetNotInteractableError` / `"option not found"` assertion contract from PYPOST-975.
- **No Scope Expansion to Sibling Tests**: While sibling tests (such as `test_live_collection_tree_index_out_of_range_raises`) may share fixtures, do not expand the diagnosis boundary beyond the named node unless diagnosis proves identical causality.
- **No Architecture in Step 1**: Technical design of diagnostic probes, tracing mechanisms, or profiling tools is deferred to Step 2.

### Functional Requirements

- **FR1 (Hypothesis Evaluation)**: The investigation must empirically test whether `apply_theme` and `uvicorn` import/execution interact concurrently in a manner that causes test delay, hang, or failure on the target node.
- **FR2 (Failure Class Determination)**: The investigation must classify the failure mechanism into one of the following evidence-backed categories:
  - *Confirmed*: A direct race condition between Qt stylesheet processing (`apply_theme`) and background uvicorn/HTTP server activity.
  - *Refuted with Alternative Identified*: The suspected Qt/uvicorn race is disproven, and an alternative mechanism (e.g., event loop starvation under CPU saturation, `is_ui_ready` polling timeout, or subprocess I/O contention) is identified and proven with data.
  - *Compound Contention*: A combination of multi-worker process scheduling pressure and Qt event dispatch latency.
- **FR3 (Comparative Differentiation)**: The output must document explicit contrasts against:
  - PYPOST-1117 (large-batch `apply_theme` segfault).
  - PYPOST-1115 / PYPOST-1040 (QWidgetItem GC teardown).
  The contrast must highlight differences in symptomology (assertion failure / timeout vs segmentation fault vs GC double-free), trigger environment (parallel 8-worker suite vs 110-module single-process batch), and execution phase.
- **FR4 (Downstream Stabilization Contract)**: The diagnostic deliverable must provide clear architectural guidelines and constraints for FIX-1 ([PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217)), specifying whether the remediation belongs in test-side fixture lifecycle management, event loop pump synchronization, process isolation, or production logic.
- **FR5 (Maintainer Documentation)**: Diagnostic conclusions and architectural findings must be documented in developer documentation for long-term maintainability.

### Non-Functional Requirements

- **NFR-1 (Empirical Rigor)**: All diagnostic claims must be supported by verifiable traces, timing data, profile metrics, or differential execution logs obtained via Make-only commands.
- **NFR-2 (Tooling Standard)**: All execution operations must strictly use `make` targets (e.g., `make test PYTEST_ARGS="..."`, `make check`), adhering to `AGENTS.md`. Raw CLI invocations (`pytest`, `flake8`, `mypy`, `pip`) are prohibited.
- **NFR-3 (Traceability & Base Commit Anchor)**: All diagnostic comparisons must anchor against the REPRO-1 baseline in `ai-tasks/PYPOST-1215/baseline-evidence.md` and base commit `353370cdbd19c7a3338e2ed05c292b0a404d7b90`.
- **NFR-4 (Isolation & Safety)**: Diagnostic tracing and probing must not leave lingering background processes, modify workspace state permanently, or cause side-effects in other test suites.

### Constraints and Assumptions

- **Baseline Dependency**: This task relies upon the empirical baseline documented in `ai-tasks/PYPOST-1215/baseline-evidence.md`.
- **Make-Only Invocation**: Direct CLI tool execution is forbidden per repository standards.
- **Behavioral Lock**: The negative interaction assertion (`session.ui_select(COLLECTION_TREE, "__no_such_collection_tree_option__")` raising `UiTargetNotInteractableError` with `"option not found"`) is a permanent behavioral lock and cannot be compromised during diagnosis or downstream fix.
- **Scope Discipline**: Diagnosis answers *why* the failure occurs; fixing *how* to prevent it is reserved for FIX-1.

### Main Entities (Business Perspective)

| Entity | Role / Description |
| --- | --- |
| **Flaky Target Node** | `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises`, the specific test exhibiting parallel flake. |
| **Suspected Race Hypothesis** | The initial hypothesis from PYPOST-1167 positing contention between Qt `apply_theme` and `uvicorn` imports/servers. |
| **Diagnostic Evidence** | Empirical data, timing profiles, logs, and stack traces captured during multi-worker execution analysis. |
| **Failure Class Taxonomy** | The structured classification of the root cause (confirmed race, event loop starvation, fixture lifecycle timing, etc.). |
| **Prior Art Baselines** | Related GUI failure modes (PYPOST-1117 large-batch segfault, PYPOST-1115 GC teardown) used for differentiation. |
| **Downstream FIX-1 Contract** | The set of architectural findings, constraints, and recommendations passed to [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217). |

## Q&A

- **Q: Why is root-cause diagnosis a dedicated story rather than being combined with the fix?**
  - **A:** Separating diagnosis (DIAG-1) from stabilization (FIX-1) ensures that each task stays within the manageable <=5 SP limit (DIAG-1 is 3 SP, FIX-1 is 3 SP), prevents applying superficial fixes to unverified root causes, and guarantees thorough documentation of concurrency mechanisms for maintainers.
- **Q: Does this task implement code changes to fix the test?**
  - **A:** No. Implementing code changes to eliminate the flake is strictly out of scope and assigned to FIX-1 ([PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217)).
- **Q: How does this task relate to REPRO-1 ([PYPOST-1215](https://pypost.atlassian.net/browse/PYPOST-1215))?**
  - **A:** REPRO-1 established the empirical evidence baseline and differential execution recipes (comparing isolated execution with parallel suite execution). DIAG-1 uses those recipes to inspect internal timing, lifecycle events, and contention mechanisms to identify the root cause.
- **Q: What if diagnosis disproves the `apply_theme` vs `uvicorn` hypothesis?**
  - **A:** If empirical evidence refutes the hypothesis, the requirement is to replace it with the true, evidence-backed failure class (e.g., Qt event loop polling latency during UI readiness checks under CPU saturation) and provide that conclusion to FIX-1.
- **Q: Why must this diagnosis explicitly distinguish from PYPOST-1117 and PYPOST-1115?**
  - **A:** PYPOST-1117 and PYPOST-1115 involve Qt styling and widget lifecycle issues in PyPost. Distinguishing them prevents maintainers from conflating distinct bugs and prevents scope creep across independent epics.
- **Q: Is a red test required in Step 3 of PYPOST-1216?**
  - **A:** In Step 2/3, the architecture will specify whether a diagnostic reproduction probe or an N/A determination (since no production code behavioral change is implemented in this diagnosis task) applies.

## References

- [PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216) — This diagnosis story (DIAG-1)
- [PYPOST-1188](https://pypost.atlassian.net/browse/PYPOST-1188) — Parent epic (Stabilize `test_live_collection_tree_missing_option_raises`)
- [PYPOST-1205](https://pypost.atlassian.net/browse/PYPOST-1205) — Epic decomposition story (`ai-tasks/PYPOST-1205/10-requirements.md`)
- [PYPOST-1215](https://pypost.atlassian.net/browse/PYPOST-1215) — Upstream baseline evidence story (REPRO-1, `ai-tasks/PYPOST-1215/baseline-evidence.md`)
- [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217) — Downstream stabilization story (FIX-1)
- [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167) — Discovery source (`ai-tasks/PYPOST-1167/60-tech-debt.md` item 6)
- [PYPOST-975](https://pypost.atlassian.net/browse/PYPOST-975) — Originating task for `COLLECTION_TREE` negative selection assertions
- [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117) — Excluded prior art epic (large-batch `apply_theme` segfault)
- [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115) — Excluded prior art epic (SettingsDialog/QWidgetItem GC teardown)
- [PYPOST-1040](https://pypost.atlassian.net/browse/PYPOST-1040) — Related SettingsDialog teardown issue
- `tests/test_ui_actions.py` — Target test node location
- `doc/dev/testing.md` — Test suite execution documentation
