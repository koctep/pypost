# PYPOST-1210: Attempt PySide6/shiboken6 pin mitigation

## Goals

Under parent epic [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115), PyPost is mitigating an intermittent native process crash (SIGSEGV/SIGBUS) occurring during Qt/PySide widget teardown. The crash was diagnosed in [PYPOST-1040](https://pypost.atlassian.net/browse/PYPOST-1040) as an upstream PySide6/shiboken6 `QWidgetItem` destructor lifecycle defect, triggered when pytest's forced cyclic garbage collection runs against `SettingsDialog`'s composite layout hierarchy.

As decomposed in [PYPOST-1203](https://pypost.atlassian.net/browse/PYPOST-1203) and governed by the evaluation contract established in MITIGATE-1 ([PYPOST-1209](https://pypost.atlassian.net/browse/PYPOST-1209)), the mitigation effort evaluates solutions in strict hierarchical sequence:
1. **MITIGATE-1 ([PYPOST-1209](https://pypost.atlassian.net/browse/PYPOST-1209))**: Evaluation contract and baseline specification (completed).
2. **MITIGATE-2 ([PYPOST-1210](https://pypost.atlassian.net/browse/PYPOST-1210))**: Attempt PySide6/shiboken6 pin mitigation (this story).
3. **MITIGATE-3 ([PYPOST-1211](https://pypost.atlassian.net/browse/PYPOST-1211))**: Attempt application-side mitigations and settle outcome (dependent on this story's outcome).

**Business Goal:** Evaluate a different PySide6/shiboken6 dependency pin (or document a justified decision not to change the pin) against the teardown stress detector, record the empirical crash-rate outcome compared to the diagnosed 32.5% baseline, and verify that functional product dialog settle e2e tests remain completely green. If a candidate pin resolves the defect completely (achieving full epic success: 0/25 crashes on the stress detector with green e2e assertions), this task assumes ownership of detector marker (`pytest.mark.xfail`) and developer documentation settlement, enabling MITIGATE-3 to be soft-skipped without orphaning settlement.

**Why pin mitigation is evaluated first:** A dependency pin upgrade or patch represents the cleanest, least invasive resolution for an upstream binding defect. If an upstream patch resolves the `QWidgetItem` destructor crash, application-side workarounds (such as manual reference-cycle breaking or post-shutdown garbage collection hooks) can be completely avoided, preventing unnecessary runtime complexity in PyPost.

## Programming Language

- **Implementation language**: Python (for dependency management, test execution, and documentation in Markdown).

## User Stories

- As a **developer / maintainer**, I want to evaluate whether an updated PySide6/shiboken6 release fixes the native teardown crash without altering application code, so that PyPost remains clean, maintainable, and aligned with upstream Qt bindings.
- As a **CI / test engineer**, I want to verify that any evaluated dependency pin maintains green functional assertions on `tests/test_agent_dialog_settle_e2e.py` and provides measurable crash-rate data against the 32.5% baseline.
- As the **implementer of MITIGATE-3 (app-side attempt)**, I want a clear empirical record of the pin candidate outcome so that I know whether to execute application-side mitigations or soft-skip my story if epic success was already achieved.
- As a **repository release gatekeeper**, I want dependency pin updates and lockfiles strictly verified via `make` quality gates (`make check`, `make check-lock`, `make verify-ai-tasks`).

## Definition of Done

This task (PYPOST-1210 / MITIGATE-2) is considered done when:

1. **Dependency Pin Evaluated**: A candidate PySide6/shiboken6 patch release (or a documented decision not to change the pin, with reason) is evaluated against the teardown stress detector.
2. **Crash-Rate Outcome Recorded**: The empirical crash rate of the candidate pin on the stress detector (`tests/test_agent_dialog_settle_teardown_stress.py` with `STRESS_ITERATIONS = 25`) is recorded and quantitatively compared against the MITIGATE-1 baseline (32.5%, 13/40).
3. **Functional Settle Assertions Preserved**: All assertions in `tests/test_agent_dialog_settle_e2e.py` (happy path and forced-timeout companion) remain green with zero regressions.
4. **Conditional Settlement Handled (Stop-on-Success Path)**:
   - If the evaluated pin satisfies Full Mitigation Success (0/25 crashes + green e2e assertions), this child story executes detector marker settlement (removing `xfail` from `tests/test_agent_dialog_settle_teardown_stress.py`), updates developer documentation (`doc/dev/agent_dialog_settle.md`), and documents the soft-skip justification for MITIGATE-3.
   - If the evaluated pin does not satisfy Full Mitigation Success, the detector marker and permanent documentation settlement are left for MITIGATE-3, while trial results and metrics are recorded in this story's artifacts.
5. **Quality Gates & Lockfiles Verified**: All repository quality gates pass (`make check`, `make check-lock`, `make verify-ai-tasks`).
6. **Task Artifacts Completed**: All Top-Down workflow artifacts (`00-roadmap.md`, `10-requirements.md`, `20-architecture.md`, etc.) are completed and verified.

## Task Description

### Problem

The PyPost dialog settle test harness intermittently encounters a native process crash (SIGSEGV/139 or SIGBUS/135) after tests report PASS. PYPOST-1040 established that this crash is caused by an upstream PySide6/shiboken6 `QWidgetItem` destructor defect when pytest's `unraisableexception` plugin forces cyclic garbage collection (`gc_collect_harder()`) on `SettingsDialog`'s nested layout hierarchy during session teardown. The baseline crash rate on PySide6 6.11.1 was measured at 32.5% (13 crashes out of 40 runs).

Under the evaluation contract defined in PYPOST-1209, MITIGATE-2 must attempt the first candidate mitigation: evaluating whether a different PySide6/shiboken6 patch version eliminates or reduces the teardown crash.

### Scope

- Identify and evaluate a candidate PySide6/shiboken6 patch version (or document a justified rationale if no viable pin change is available).
- Execute the teardown stress detector (`tests/test_agent_dialog_settle_teardown_stress.py` with `STRESS_ITERATIONS = 25`) against the candidate pin.
- Measure and record the empirical crash rate vs the 32.5% baseline.
- Execute the functional dialog settle suite (`tests/test_agent_dialog_settle_e2e.py`) to confirm zero functional regressions.
- If Full Mitigation Success is achieved (0/25 crashes + green e2e), perform detector marker settlement (un-xfail stress test) and dev doc updates in `doc/dev/agent_dialog_settle.md`, logging the soft-skip justification for MITIGATE-3.
- If Full Mitigation Success is not achieved, record the outcome to serve as input for MITIGATE-3.

### Out of Scope

- Writing or altering the evaluation contract or baseline definition (owned by MITIGATE-1 / [PYPOST-1209](https://pypost.atlassian.net/browse/PYPOST-1209)).
- Implementing application-side cycle-breaking or lifecycle modifications in `pypost/` (reserved for MITIGATE-3 / [PYPOST-1211](https://pypost.atlassian.net/browse/PYPOST-1211) if the pin attempt does not achieve epic success).
- Re-diagnosing the root cause or mechanism diagnosed in [PYPOST-1040](https://pypost.atlassian.net/browse/PYPOST-1040).
- Addressing duration-report xfail labeling ([PYPOST-1116](https://pypost.atlassian.net/browse/PYPOST-1116)) or batch GUI stability debt ([PYPOST-1070](https://pypost.atlassian.net/browse/PYPOST-1070)).
- Guaranteeing an upstream fix from Qt/The Qt Company.

### Functional Requirements

- **FR1 (Candidate Pin Selection & Evaluation)**: The system must evaluate an alternative PySide6/shiboken6 patch release against the teardown stress detector, or provide a documented technical justification for retaining the existing pin.
- **FR2 (Statistical Crash-Rate Measurement)**: The candidate pin must be executed through the 25-iteration teardown stress detector (`tests/test_agent_dialog_settle_teardown_stress.py`), recording the exact number of child process crashes (SIGSEGV/SIGBUS exit codes).
- **FR3 (Baseline Comparison & Recording)**: The observed crash rate must be compared against the 32.5% baseline established in MITIGATE-1 and documented in the task artifacts.
- **FR4 (Functional Settle Verification)**: Both the happy-path modal settle and the forced-timeout companion in `tests/test_agent_dialog_settle_e2e.py` must pass with all assertion and logging contracts intact.
- **FR5 (Conditional Settlement Execution)**:
  - When the candidate pin achieves 0/25 crashes and green e2e assertions (Full Mitigation Success):
    - Remove `pytest.mark.xfail` from `tests/test_agent_dialog_settle_teardown_stress.py`.
    - Update `doc/dev/agent_dialog_settle.md` with the pin mitigation resolution.
    - Record the authorization to soft-skip MITIGATE-3.
  - When the candidate pin results in $\ge 1$ crash out of 25:
    - Retain `pytest.mark.xfail(strict=False)` on the stress detector.
    - Record findings to hand off settlement ownership to MITIGATE-3.
- **FR6 (Dependency Lock Integrity)**: If any dependency change is made in `pyproject.toml`, lockfiles and environment installations must be cleanly synchronized and validated via `make` targets.

### Non-Functional Requirements

- **NFR1 (Statistical Rigor)**: Evaluation must utilize the standard sample size ($N = 25$) providing $>99.99\%$ statistical power against the baseline crash rate ($p = 0.325$).
- **NFR2 (Minimal Intervention)**: Prioritize clean dependency-level mitigation to avoid injecting unnecessary workaround code into production application paths.
- **NFR3 (Settlement Invariant)**: Settlement ownership must strictly obey the MITIGATE-1 contract: settlement is performed by MITIGATE-2 if and only if epic success is met; otherwise settlement is deferred to MITIGATE-3.
- **NFR4 (Quality Standard & Tooling Compliance)**: All checks, tests, and verifications must strictly execute via `make` targets (`make check`, `make check-lock`, `make verify-ai-tasks`).

### Constraints and Assumptions

- The evaluation contract, baseline facts, and stop-on-success rules defined in MITIGATE-1 ([PYPOST-1209](https://pypost.atlassian.net/browse/PYPOST-1209)) and `doc/dev/agent_dialog_settle.md` are binding.
- Only official PySide6 / shiboken6 wheels compatible with Python 3.11+ / 3.13 and the PyPost platform matrix can be evaluated.
- All operations must adhere to the Make-only tooling standard without direct CLI tool invocations.

### Main Entities (Business & Evaluation Domain)

| Entity | Description / Role |
| --- | --- |
| **Candidate Dependency Pin** | The specific PySide6 / shiboken6 version evaluated as a potential upstream fix for the `QWidgetItem` GC crash. |
| **Teardown Stress Detector** | The subprocess-based test harness (`tests/test_agent_dialog_settle_teardown_stress.py`, N=25) used to measure process stability. |
| **Functional Settle Suite** | The e2e test suite (`tests/test_agent_dialog_settle_e2e.py`) validating modal settle, timeout diagnostics, and DEBUG logging contracts. |
| **Empirical Crash-Rate Outcome** | The measured crash count ($k / 25$) resulting from the candidate evaluation, compared against the 32.5% baseline. |
| **Stop-on-Success Path** | The execution branch activated if $k = 0$, triggering marker settlement and enabling the soft-skip of MITIGATE-3. |
| **Settlement Action** | The update of `pytest.mark.xfail` on the stress detector and corresponding updates to `doc/dev/agent_dialog_settle.md`. |

## Q&A

- **Q: Why is pin evaluation performed in its own story (MITIGATE-2)?**
  - A: Separating pin evaluation from application-side work isolates dependency-level trials from code refactoring. This keeps changes atomic, clear, and easily revertible if a pin change introduces side-effects.
- **Q: What constitutes "Full Mitigation Success" for this story?**
  - A: Exactly 0 crashes out of 25 runs on `tests/test_agent_dialog_settle_teardown_stress.py` and zero regressions on `tests/test_agent_dialog_settle_e2e.py`.
- **Q: What happens if the pin candidate crashes 1 or more times out of 25?**
  - A: Any outcome with $\ge 1$ crash does not satisfy the stop-on-success criterion. The trial outcome is recorded in this story's artifacts, the stress detector remains marked `xfail`, and execution proceeds to MITIGATE-3 for application-side mitigations.
- **Q: Under what circumstances does MITIGATE-2 modify the stress detector's `xfail` marker?**
  - A: MITIGATE-2 modifies (removes) the `xfail` marker if and only if the candidate pin achieves 0/25 crashes and green e2e assertions, thereby completing epic success and soft-skipping MITIGATE-3.
- **Q: What happens if no newer patch release exists or is compatible?**
  - A: The evaluation documents the rationale for retaining the current pin (e.g. latest available patch already tested or incompatibilities identified), records the baseline crash rate, and passes execution to MITIGATE-3.

## References

- [PYPOST-1210](https://pypost.atlassian.net/browse/PYPOST-1210) — this task (MITIGATE-2)
- [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115) — parent epic (mitigate QWidgetItem GC-teardown crash)
- [PYPOST-1203](https://pypost.atlassian.net/browse/PYPOST-1203) — epic decomposition story
- [PYPOST-1209](https://pypost.atlassian.net/browse/PYPOST-1209) — MITIGATE-1 (evaluation contract & baseline)
- [PYPOST-1211](https://pypost.atlassian.net/browse/PYPOST-1211) — MITIGATE-3 (app-side attempt + settlement)
- [PYPOST-1040](https://pypost.atlassian.net/browse/PYPOST-1040) — diagnostic investigation of the teardown crash
- `doc/dev/agent_dialog_settle.md` — developer documentation for dialog settle, evaluation contract, and teardown stress
- `tests/test_agent_dialog_settle_teardown_stress.py` — teardown stress detector
- `tests/test_agent_dialog_settle_e2e.py` — product dialog settle e2e suite
- `pyproject.toml` — project dependency specifications
