# PYPOST-1211: Attempt application-side mitigations and settle outcome

## Goals

Under parent epic [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115), PyPost is mitigating an intermittent native process crash (SIGSEGV/SIGBUS) occurring during Qt/PySide widget teardown. The crash was diagnosed in [PYPOST-1040](https://pypost.atlassian.net/browse/PYPOST-1040) as an upstream PySide6/shiboken6 `QWidgetItem` destructor lifecycle defect, triggered when pytest's forced cyclic garbage collection (`gc_collect_harder()`) runs against `SettingsDialog`'s composite layout hierarchy at session teardown.

The mitigation hierarchy established in [PYPOST-1203](https://pypost.atlassian.net/browse/PYPOST-1203) and governed by the evaluation contract in MITIGATE-1 ([PYPOST-1209](https://pypost.atlassian.net/browse/PYPOST-1209)) defines three stories:
1. **MITIGATE-1 ([PYPOST-1209](https://pypost.atlassian.net/browse/PYPOST-1209))**: Evaluation contract and baseline specification (completed).
2. **MITIGATE-2 ([PYPOST-1210](https://pypost.atlassian.net/browse/PYPOST-1210))**: Attempt PySide6/shiboken6 pin mitigation (completed — evaluated and determined that no viable upstream patch exists; the 32.5% baseline defect persists under the pinned dependency).
3. **MITIGATE-3 ([PYPOST-1211](https://pypost.atlassian.net/browse/PYPOST-1211))**: Attempt application-side mitigations and settle outcome (this story).

**Business Goal:** Evaluate application-side mitigations (breaking reference cycles in `SettingsDialog` composite layout hierarchies and/or executing controlled post-shutdown garbage collection in `AgentAppSession`, or recording a reasoned technical decision) against the teardown stress detector; record the empirical crash-rate outcome against the diagnosed 32.5% baseline; preserve green functional product dialog settle e2e assertions; and own final detector marker (`pytest.mark.xfail`) and developer documentation settlement for epic PYPOST-1115.

**Why application-side mitigation is evaluated now:** The dependency pin evaluation in MITIGATE-2 confirmed that no upstream Qt/PySide6 release resolves the `QWidgetItem` destructor crash in the active release line. Application-side cycle breaking and lifecycle management represent the final internal mitigation layer available to eliminate or reduce the teardown crash before settling the outcome and documenting any residual upstream debt.

## Programming Language

- **Implementation language**: Python (for application UI lifecycle handling, test execution, and Markdown documentation).

## User Stories

- As a **developer / maintainer**, I want to evaluate whether breaking layout reference cycles or controlling garbage collection timing eliminates the native teardown crash, so that PyPost application and test environments run reliably without unexpected process termination.
- As a **CI / test engineer**, I want to verify that all functional dialog settle e2e tests (`tests/test_agent_dialog_settle_e2e.py`) remain completely green with zero assertion or diagnostic logging regressions while executing under application-side mitigations.
- As a **quality gatekeeper**, I want the final status of the teardown stress detector (`pytest.mark.xfail`) and developer documentation (`doc/dev/agent_dialog_settle.md`) to be definitively settled based on empirical evidence from 25 stress test runs.
- As an **architect / release manager**, I want any unresolved upstream limitations to be clearly documented in technical debt and developer guides so that the team understands the system's operational boundaries and future upgrade paths.

## Definition of Done

This task (PYPOST-1211 / MITIGATE-3) is considered done when:

1. **Application-Side Mitigations Evaluated**: Layout reference cycle breaking in `SettingsDialog` and/or controlled post-shutdown `gc.collect()` in `AgentAppSession` (or a reasoned technical decision with justification) is implemented and evaluated against the stress detector.
2. **Crash-Rate Outcome Recorded**: The empirical crash rate of the application-side mitigation is measured across `STRESS_ITERATIONS = 25` runs on `tests/test_agent_dialog_settle_teardown_stress.py` and compared against the 32.5% baseline (13/40) and MITIGATE-2 findings.
3. **Functional Settle Assertions Preserved**: All functional dialog settle assertions and diagnostic contracts in `tests/test_agent_dialog_settle_e2e.py` (happy-path modal settle and forced-timeout companion) remain 100% green with zero regressions.
4. **Final Detector Marker Settlement Executed**:
   - If Full Mitigation Success (0/25 crashes + green e2e) is achieved: remove `pytest.mark.xfail` from `tests/test_agent_dialog_settle_teardown_stress.py`.
   - If Full Mitigation Success is not achieved ($\ge 1$ crash in 25 runs): retain `pytest.mark.xfail(strict=False)` with documented trial history.
5. **Developer Documentation & Tech Debt Settled**: `doc/dev/agent_dialog_settle.md` is updated with the final mitigation outcome, settlement disposition, and technical debt analysis for epic PYPOST-1115.
6. **Quality Gates Verified**: All repository quality gates pass strictly via Make targets (`make check`, `make verify-ai-tasks`).
7. **Task Artifacts Completed**: All Top-Down workflow artifacts (`00-roadmap.md`, `10-requirements.md`, `20-architecture.md`, `40-code-cleanup.md`, `50-observability.md`, `60-tech-debt.md`) are completed.

## Task Description

### Problem

During test session teardown of the product dialog settle suite, pytest's `unraisableexception` plugin invokes cyclic garbage collection (`gc_collect_harder()`), which triggers an upstream PySide6/shiboken6 `QWidgetItem` C++ destructor crash on Linux when destroying `SettingsDialog`'s composite widget and layout hierarchy. PYPOST-1040 established the root cause and a 32.5% baseline crash rate. MITIGATE-2 ([PYPOST-1210](https://pypost.atlassian.net/browse/PYPOST-1210)) evaluated the dependency pin and determined that no upstream patch exists, retaining the `PySide6==6.11.1` pin and transferring settlement ownership to MITIGATE-3.

MITIGATE-3 must now evaluate application-side mitigations to break layout reference cycles or decouple garbage collection timing, measure process stability against the stress detector, and finalize the settlement of test markers and documentation.

### Scope

- Evaluate application-side mitigation candidates:
  - Breaking layout reference cycles in `SettingsDialog` composite sections.
  - Controlling post-shutdown garbage collection in `AgentAppSession`.
- Execute the 25-iteration teardown stress detector (`tests/test_agent_dialog_settle_teardown_stress.py`) to determine process crash rate vs the 32.5% baseline.
- Execute the functional dialog settle suite (`tests/test_agent_dialog_settle_e2e.py`) to verify zero behavioral or diagnostic regressions.
- Execute final settlement of the stress detector marker (`pytest.mark.xfail`):
  - Path B (Success): Un-xfail detector if 0/25 crashes achieved.
  - Path C (Exhaustion / Upstream): Retain xfail if $\ge 1$ crash occurs.
- Update developer documentation in `doc/dev/agent_dialog_settle.md` with final empirical results, settlement rationale, and technical debt notes.
- Document technical debt and close epic PYPOST-1115 settlement ownership.

### Out of Scope

- Modifying the evaluation contract or baseline specification (owned by MITIGATE-1 / [PYPOST-1209](https://pypost.atlassian.net/browse/PYPOST-1209)).
- Upstream PySide6 / Qt C++ source modifications.
- Addressing duration-report xfail labeling ([PYPOST-1116](https://pypost.atlassian.net/browse/PYPOST-1116)) or batch GUI stability debt ([PYPOST-1070](https://pypost.atlassian.net/browse/PYPOST-1070)).
- Altering the fundamental business functionality of Settings dialog sections.

### Functional Requirements

- **FR1 (Application-Side Mitigation Evaluation)**: The system must evaluate at least one application-side mitigation strategy (such as layout reference cycle breaking in `SettingsDialog` or deliberate post-shutdown `gc.collect()` in `AgentAppSession`, or document a reasoned technical decision) aimed at preventing the `QWidgetItem` destructor crash.
- **FR2 (Statistical Stability Measurement)**: The system must execute the 25-iteration teardown stress detector (`tests/test_agent_dialog_settle_teardown_stress.py`) to measure the crash frequency ($k / 25$) of the application-side mitigation.
- **FR3 (Baseline Comparative Analysis)**: The empirical crash rate must be quantitatively compared against the 32.5% baseline (13/40) established in MITIGATE-1 and the MITIGATE-2 pin evaluation findings.
- **FR4 (Functional Preservation Verification)**: The functional dialog settle suite (`tests/test_agent_dialog_settle_e2e.py`) must pass with 100% green status, verifying that:
  - The happy-path modal settle and dismiss workflow functions correctly.
  - Forced-timeout diagnostic rewraps (`step=wait_dialog_after_settings_open`) and modal scalar diagnostics remain intact.
  - DEBUG event logging contracts (`pypost.agent.ui_wait`, `condition=forced_dialog_settle_timeout`) remain intact.
- **FR5 (Deterministic Settlement Execution)**:
  - If the application-side mitigation achieves Full Mitigation Success (0/25 crashes and green e2e assertions):
    - Update `tests/test_agent_dialog_settle_teardown_stress.py` to remove `pytest.mark.xfail`.
    - Update `doc/dev/agent_dialog_settle.md` to document the successful application-side resolution.
  - If the application-side mitigation does not achieve Full Mitigation Success ($\ge 1$ crash out of 25):
    - Retain `@pytest.mark.xfail(reason="...", strict=False)` on `tests/test_agent_dialog_settle_teardown_stress.py`.
    - Update `doc/dev/agent_dialog_settle.md` to record the trial outcome and permanent upstream defect classification.
- **FR6 (Developer Documentation & Tech Debt Updates)**: Developer documentation in `doc/dev/agent_dialog_settle.md` and task technical debt artifacts must reflect the final outcome, trial metrics, and residual debt disposition.

### Non-Functional Requirements

- **NFR1 (Statistical Rigor)**: Evaluation must execute $N = 25$ independent child processes to ensure $>99.99\%$ statistical confidence against the baseline defect rate ($p = 0.325$).
- **NFR2 (Contract Preservation)**: Application-side modifications must not alter public APIs, UI behaviors, or diagnostic error formatting of the dialog settle subsystem.
- **NFR3 (Deterministic Settlement)**: Settlement of test markers and dev documentation must be completed definitively within this story, leaving zero orphaned markers or unassigned decisions for epic PYPOST-1115.
- **NFR4 (Tooling Standard Compliance)**: All test runs, quality gates, and verifications must strictly use `make` targets (`make check`, `make verify-ai-tasks`).

### Constraints and Assumptions

- The evaluation contract and decision rules established in MITIGATE-1 ([PYPOST-1209](https://pypost.atlassian.net/browse/PYPOST-1209)) and `doc/dev/agent_dialog_settle.md` are binding.
- MITIGATE-2 ([PYPOST-1210](https://pypost.atlassian.net/browse/PYPOST-1210)) evaluated dependency pins and retained `PySide6==6.11.1`, transferring settlement ownership to this story (PYPOST-1211).
- Operating environment is Linux under containerized offscreen execution (`QT_QPA_PLATFORM=offscreen`).
- Direct invocation of raw CLI tools (e.g. `pytest`, `flake8`) is strictly prohibited per repository rules.

### Main Entities (Business & Evaluation Domain)

| Entity | Description / Role |
| --- | --- |
| **Application-Side Mitigation** | Code adjustments in `SettingsDialog` layout hierarchy or `AgentAppSession` teardown designed to break reference cycles or manage GC timing. |
| **Teardown Stress Detector** | Sibling test suite (`tests/test_agent_dialog_settle_teardown_stress.py`, N=25) providing empirical process stability measurement. |
| **Functional Settle Suite** | Product dialog settle test suite (`tests/test_agent_dialog_settle_e2e.py`) verifying modal settle, timeout diagnostics, and DEBUG logging. |
| **Empirical Crash-Rate Outcome** | The measured crash rate ($k / 25$) compared against the 32.5% baseline. |
| **Settlement Decision (Path B vs Path C)** | The deterministic branching decision resolving whether to un-xfail the stress detector (Path B) or retain xfail with permanent upstream debt (Path C). |
| **Epic Settlement** | Final closure of epic PYPOST-1115 with updated developer documentation and test markers. |

## Q&A

- **Q: Why does PYPOST-1211 own final settlement?**
  - A: Under the deterministic settlement model in `doc/dev/agent_dialog_settle.md`, MITIGATE-2 only owns settlement if pin mitigation achieves 0/25 crashes (Path A). Because MITIGATE-2 determined that no upstream patch exists, settlement ownership transferred to MITIGATE-3 to either settle as Path B (app-side success) or Path C (permanent upstream exhaustion).
- **Q: What criteria define Full Mitigation Success for an application-side mitigation?**
  - A: Exactly 0 crashes out of 25 runs on `tests/test_agent_dialog_settle_teardown_stress.py` and green functional assertions on `tests/test_agent_dialog_settle_e2e.py`.
- **Q: What happens if an application-side mitigation reduces crashes from 8/25 to 1/25?**
  - A: Any outcome with $\ge 1$ crash in 25 runs does not satisfy the zero-crash threshold. Process teardown remains vulnerable; therefore, the `xfail` marker is retained and the limitation is documented as residual technical debt.
- **Q: How does this story ensure functional preservation?**
  - A: By verifying that both happy-path modal settle and forced-timeout diagnostics (including DEBUG logger records and exception diagnostics) in `tests/test_agent_dialog_settle_e2e.py` remain fully functional and green.
- **Q: Which developer documentation must be updated?**
  - A: `doc/dev/agent_dialog_settle.md` must be updated with the empirical trial results, the final settlement status of the stress detector marker, and the epic disposition.

## References

- [PYPOST-1211](https://pypost.atlassian.net/browse/PYPOST-1211) — this task (MITIGATE-3: application-side mitigation and settlement)
- [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115) — parent epic (mitigate QWidgetItem GC-teardown crash)
- [PYPOST-1203](https://pypost.atlassian.net/browse/PYPOST-1203) — epic decomposition story
- [PYPOST-1209](https://pypost.atlassian.net/browse/PYPOST-1209) — MITIGATE-1 (evaluation contract & baseline specification)
- [PYPOST-1210](https://pypost.atlassian.net/browse/PYPOST-1210) — MITIGATE-2 (PySide6/shiboken6 pin evaluation)
- [PYPOST-1040](https://pypost.atlassian.net/browse/PYPOST-1040) — teardown crash diagnostic investigation
- `doc/dev/agent_dialog_settle.md` — developer documentation and mitigation evaluation contract
- `tests/test_agent_dialog_settle_teardown_stress.py` — teardown stress detector
- `tests/test_agent_dialog_settle_e2e.py` — product dialog settle e2e test suite
