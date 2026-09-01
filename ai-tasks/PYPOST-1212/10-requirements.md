# PYPOST-1212: [PYPOST-1117] Deterministic repro and evidence baseline for large-batch apply_theme segfault

## Goals

During test suite verification in [PYPOST-1070](https://pypost.atlassian.net/browse/PYPOST-1070), running the full batch of ~110 GUI-heavy test modules in a single pytest process resulted in a native segmentation fault (`SIGSEGV`, exit code 139) originating from `pypost/ui/styles/style_manager.py:102` during `apply_theme` (specifically around `app.setStyle(...)` and `QStyleFactory.create("Fusion")`). In contrast, running individual test modules or running the suite partitioned into 8 bounded batches (~1,384 tests total) completed cleanly with all tests passing.

This issue was promoted to epic [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117) and decomposed in [PYPOST-1204](https://pypost.atlassian.net/browse/PYPOST-1204) into three sequential stories:
1. **REPRO-1 ([PYPOST-1212](https://pypost.atlassian.net/browse/PYPOST-1212))**: Deterministic repro and evidence baseline (this task).
2. **DIAG-1 ([PYPOST-1213](https://pypost.atlassian.net/browse/PYPOST-1213))**: Root-cause diagnosis (shared Shiboken/Qt lifetime vs distinct QStyle/QPalette accumulation).
3. **MITIGATE-1 ([PYPOST-1214](https://pypost.atlassian.net/browse/PYPOST-1214))**: Safe mitigation and CI ownership documentation.

**Business Goal:** Provide a documented, repeatable subprocess-level reproduction procedure and a comprehensive evidence baseline (environment specifications, exact execution commands, failure logs, and the empirical contrast between failing full batches and passing bounded/individual runs) so that downstream diagnostic and mitigation tasks can cite, execute, and verify against a stable baseline without needing to re-derive reproduction parameters from PYPOST-1070 notes.

**Why Repro & Baseline Matter:** Native crashes (SIGSEGV) in PySide6/Qt desktop applications undermine developer productivity and continuous integration reliability. Without a deterministic, isolated reproduction procedure and an objective baseline, engineers diagnosing the root cause (DIAG-1) or implementing mitigations (MITIGATE-1) would rely on anecdotal trial-and-error, risking incomplete fixes or unverified assumptions.

## Programming Language

- **Implementation language**: Python (for test harness, execution scripts, and verification procedures), with English Markdown for documentation and baseline artifacts.

## User Stories

- As a **diagnostician / developer working on DIAG-1 ([PYPOST-1213](https://pypost.atlassian.net/browse/PYPOST-1213))**, I want a documented, repeatable subprocess-level procedure that reproduces the large-batch native crash alongside baseline evidence, so I can investigate root causes (e.g. Shiboken/Qt object lifetime vs QStyle/QPalette accumulation) on top of a reliable foundation without re-discovering reproduction parameters from scratch.
- As an **engineer implementing mitigations in MITIGATE-1 ([PYPOST-1214](https://pypost.atlassian.net/browse/PYPOST-1214))**, I want a structured pass/fail baseline and workload profile, so I can verify whether bounded batching or process isolation eliminates the native crash under identical stress conditions.
- As a **CI owner / release engineer**, I want clear documentation of the failure site, execution environment, and the contrast between large single-process batches and bounded batches, so future test infrastructure decisions are backed by empirical evidence.
- As a **PyPost maintainer**, I want the crash observation tied to the `apply_theme` / style-factory site and kept explicitly distinct from the SettingsDialog GC teardown crash ([PYPOST-1040](https://pypost.atlassian.net/browse/PYPOST-1040) / [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115)), so that distinct native memory defects in the Qt/PySide layer are tracked and resolved independently.

## Definition of Done

This task is considered `done` when:

1. A documented, repeatable subprocess-level procedure is established that reproduces the large-batch Qt/PySide6 GUI test native crash (or a justified equivalent matching the epic crash site and load class).
2. A comprehensive baseline evidence record is created documenting:
   - Environment parameters (operating system, Python version, Qt/PySide6 bindings version, offscreen platform settings).
   - Exact command shape and batch parameters used for execution.
   - Empirical contrast demonstrating that bounded test batches and individual test modules pass cleanly, while the full large-batch execution fails natively.
3. The crash observation is specifically tied to the known `apply_theme` / style-factory site (`pypost/ui/styles/style_manager.py:102` or updated with evidence if the repro surfaces a refined location).
4. Deliverables are organized and recorded such that downstream tasks (DIAG-1 / PYPOST-1213 and MITIGATE-1 / PYPOST-1214) can cite and run the baseline without re-deriving details from PYPOST-1070.
5. All repo tooling rules are adhered to (Make-only execution, non-blocking boundaries, clear separation from other tickets).

## Task Description

### Problem Description

When running large collections of GUI-heavy test modules (e.g. ~110 modules) in a single pytest process with `QT_QPA_PLATFORM=offscreen`, the process crashes with a native segmentation fault (`SIGSEGV` / exit code 139) inside `pypost/ui/styles/style_manager.py:102` during `apply_theme` calls (`app.setStyle(...)` / `QStyleFactory.create("Fusion")`).

However:
- Each test module passes when executed in isolation.
- The full suite passes when split into 8 bounded batches (~1,384 tests).
- The failure is independent of the test refactoring done in PYPOST-1070 (reproduces against pre-refactor test files).

Currently, this finding exists only as a note in `ai-tasks/PYPOST-1070/60-tech-debt.md`. To enable DIAG-1 and MITIGATE-1, this task must formalize a standalone, repeatable subprocess-level reproduction procedure and document the empirical baseline.

### Scope

- Establish a reliable, subprocess-level procedure to reproduce the native segfault under large-batch GUI test load.
- Gather and document the complete baseline evidence record:
  - System and runtime environment specs (Linux, Python 3.11/3.13, PySide6, headless/offscreen configuration).
  - Command invocations and arguments.
  - Failure signatures (exit code 139 / SIGSEGV, stderr backtraces, crash site).
  - Contrast evidence showing successful execution of bounded batches and individual modules.
- Attribute the crash to the specific `apply_theme` / style-factory surface (or record evidence if the location shifts under stress).
- Package the procedure and evidence so it can be cited by PYPOST-1213 and PYPOST-1214.

### Out of Scope (Non-Goals)

- Determining the root-cause class (e.g., whether it is deferred cyclic GC of Shiboken wrappers vs QStyle/QPalette object accumulation under repeated theme changes) — this belongs to **DIAG-1 ([PYPOST-1213](https://pypost.atlassian.net/browse/PYPOST-1213))**.
- Implementing bounded batching, process isolation, or modifying CI test policies — this belongs to **MITIGATE-1 ([PYPOST-1214](https://pypost.atlassian.net/browse/PYPOST-1214))**.
- Merging scope with the SettingsDialog / QWidgetItem teardown GC crash ([PYPOST-1040](https://pypost.atlassian.net/browse/PYPOST-1040) / [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115)), which represents a distinct crash site and trigger.
- Modifying production application code in `pypost/ui/styles/style_manager.py` or production styling behavior.
- Resolving pre-existing non-crash suite failures tracked in separate tickets (e.g., PYPOST-1110, PYPOST-1111).

### Functional Requirements

- **FR-1: Repeatable Subprocess Repro Procedure**: The deliverable must provide an automated or scripted subprocess-level execution procedure that consistently triggers the large-batch native crash under the documented load conditions.
- **FR-2: Baseline Environment Documentation**: The deliverable must record the exact runtime environment parameters, including OS, Python version, PySide6/Qt versions, environment variables (e.g. `QT_QPA_PLATFORM=offscreen`), and hardware/process context.
- **FR-3: Pass/Fail Contrast Documentation**: The deliverable must provide verifiable evidence demonstrating that individual test modules and bounded batches pass cleanly, establishing that the failure is specific to process-accumulated large-batch load.
- **FR-4: Crash Site Attribution**: The deliverable must identify and record the crash site (`pypost/ui/styles/style_manager.py:102` / `app.setStyle` / `QStyleFactory.create("Fusion")`) with supporting trace data, or record precise evidence if the site varies.
- **FR-5: Citable Artifact for Child Tasks**: The repro procedure and baseline evidence must be structured so that DIAG-1 (PYPOST-1213) and MITIGATE-1 (PYPOST-1214) can cite and execute them directly without re-investigating reproduction steps.

### Non-Functional Requirements

- **NFR-1: Determinism & Repeatability**: The reproduction procedure must yield repeatable results across test runs in matching environments.
- **NFR-2: Subprocess Safety & Containment**: Reproduction runs must execute in isolated subprocesses so that native SIGSEGV crashes do not abruptly terminate parent orchestration or test runners.
- **NFR-3: Evidence Fidelity & Traceability**: All logs, terminal outputs, error messages, and process exit codes must be accurately captured and preserved without alteration.
- **NFR-4: Make-Only Compliance**: All commands and verification steps must align with repository Make targets and tooling standards.
- **NFR-5: Clarity & Modularity**: The documented baseline must be concise, self-contained, and easily consumed by subsequent development steps.

### Constraints and Assumptions

- **Host Environment**: The primary target environment is Linux with Python 3.11 / 3.13, PySide6, and offscreen Qt platform (`QT_QPA_PLATFORM=offscreen`).
- **Native Crash Characteristics**: The defect manifests as an operating system signal (`SIGSEGV`, exit code 139) or native C++ binding abort during Qt style manipulation under sustained process execution.
- **Independence from Code Changes**: The reproduction does not depend on modifications to product code or tests.
- **Distinct from PYPOST-1040/1115**: The crash occurs in `style_manager.py` during `apply_theme` across large batches, whereas PYPOST-1040/1115 is a `SettingsDialog` / `QWidgetItem` GC crash at session end.

### Main Business Entities

| Entity | Description / Role |
| --- | --- |
| **Large-Batch GUI Workload** | The collective execution of ~110 GUI-heavy test modules in a single pytest process that triggers the native crash. |
| **Bounded Test Batch** | Subdivided batches of GUI test modules (e.g. 8 chunked batches of ~1,384 tests) that execute successfully without crashing. |
| **Individual Test Module** | A single test file that passes completely in isolation. |
| **Reproduction Procedure** | The documented, repeatable subprocess-level command/script that invokes the workload and reproduces the failure. |
| **Baseline Evidence Record** | The structured artifact capturing environment details, commands, stdout/stderr logs, exit codes, and contrast analysis. |
| **Crash Surface (`apply_theme`)** | The code site (`pypost/ui/styles/style_manager.py:102`) where native Qt/PySide6 style application fails under accumulated load. |
| **Downstream Tasks** | DIAG-1 (PYPOST-1213) and MITIGATE-1 (PYPOST-1214) which consume the repro procedure and baseline evidence. |

## Q&A

- **Q1: Why is this task scoped only to reproduction and baseline evidence rather than diagnosing the root cause?**
  - *A*: Per the decomposition of epic PYPOST-1117 in PYPOST-1204, separating reproduction (REPRO-1 / PYPOST-1212), root-cause diagnosis (DIAG-1 / PYPOST-1213), and mitigation (MITIGATE-1 / PYPOST-1214) keeps each task within preferred sizing (≤5 SP) and allows rigorous, evidence-gated progression through Top-Down steps.
- **Q2: Does this task implement a fix or change CI batching configurations?**
  - *A*: No. Implementing mitigations (such as bounded batching or process isolation in CI) is explicitly owned by MITIGATE-1 (PYPOST-1214).
- **Q3: How is this crash different from PYPOST-1040 / PYPOST-1115?**
  - *A*: PYPOST-1040 / PYPOST-1115 investigated a `SIGSEGV` during `SettingsDialog` teardown (`Shiboken::callCppDestructor<QWidgetItem>`) occurring during post-PASS forced GC. This task investigates a native crash in `apply_theme` (`app.setStyle` / `QStyleFactory.create("Fusion")`) occurring under sustained large-batch test execution across many modules.
- **Q4: What constitutes acceptable baseline evidence?**
  - *A*: Full environment details (OS, Python version, PySide6 version, Qt offscreen flags), exact command invocations, captured exit codes and error output, and explicit demonstration that bounded batches and individual modules pass cleanly while the large batch fails.
- **Q5: Will product code in `pypost/` be modified in this task?**
  - *A*: No product code modifications are expected; this task produces the reproduction mechanism, verification tests/harness, and baseline documentation.

## References

- Epic: [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117) — Diagnose large-batch Qt/PySide6 GUI test segfault in `apply_theme`
- Decompose Story: [PYPOST-1204](https://pypost.atlassian.net/browse/PYPOST-1204) — Decompose epic PYPOST-1117
- Source Tech Debt: `ai-tasks/PYPOST-1070/60-tech-debt.md` (discovery notes and batch contrast)
- Related Prior Art: `ai-tasks/PYPOST-1040/20-architecture.md` / [PYPOST-1040](https://pypost.atlassian.net/browse/PYPOST-1040) (distinct teardown GC crash)
- Downstream Tasks: [PYPOST-1213](https://pypost.atlassian.net/browse/PYPOST-1213) (DIAG-1), [PYPOST-1214](https://pypost.atlassian.net/browse/PYPOST-1214) (MITIGATE-1)
- Crash Surface: `pypost/ui/styles/style_manager.py` (`apply_theme`)
