# PYPOST-1209: Document mitigation evaluation contract and baseline

## Goals

Epic [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115) aims to mitigate an intermittent native SIGSEGV/SIGBUS process crash occurring during Qt/PySide widget teardown. The crash was diagnosed in [PYPOST-1040](https://pypost.atlassian.net/browse/PYPOST-1040) as an upstream PySide6/shiboken6 `QWidgetItem` lifecycle defect triggered when pytest's forced cyclic garbage collection acts on `SettingsDialog`'s nested-layout subtree. Epic PYPOST-1115 was subsequently decomposed in [PYPOST-1203](https://pypost.atlassian.net/browse/PYPOST-1203) into three focused, implementable child stories:
1. **MITIGATE-1 ([PYPOST-1209](https://pypost.atlassian.net/browse/PYPOST-1209))**: Document mitigation evaluation contract and baseline (this story).
2. **MITIGATE-2 ([PYPOST-1210](https://pypost.atlassian.net/browse/PYPOST-1210))**: Attempt PySide6/shiboken6 pin mitigation.
3. **MITIGATE-3 ([PYPOST-1211](https://pypost.atlassian.net/browse/PYPOST-1211))**: Attempt application-side mitigations and settle outcome.

**Business Goal:** Establish an explicit, shared evaluation contract and baseline for the mitigation effort under epic PYPOST-1115. This ensures that downstream implementation children (MITIGATE-2 and MITIGATE-3) execute with unambiguous, pre-agreed standards for what constitutes a "materially reduced" crash rate, follow a standardized candidate trial sequence, adhere to strict stop-on-success rules without leaving test markers or developer documentation orphaned, and measure results against verified, shared proof surfaces.

**Why this contract is needed:** Without a shared evaluation contract defined prior to implementation, individual mitigation attempts risk adopting inconsistent benchmarks, debating whether an observed crash-rate reduction is sufficient, prematurely halting exploration, or orphaning the final settlement of test markers (`xfail`) and documentation across different success paths.

## Programming Language

- **Implementation language**: Python (for repository test harness execution, verification scripts, and developer documentation in Markdown).

## User Stories

- As a **sprint planner / maintainer**, I want an explicit evaluation contract and baseline defined before mitigation tickets run, so that all child stories share identical definitions of success, ordering, and stop conditions without ad-hoc negotiations.
- As an **implementer of MITIGATE-2 (pin attempt)**, I want clear quantitative criteria for what constitutes a "materially reduced" crash rate, and explicit rules on whether I must settle the stress detector marker and dev docs if stop-on-success permits soft-skipping MITIGATE-3.
- As an **implementer of MITIGATE-3 (app-side attempt)**, I want unambiguous baseline figures and proof surfaces to evaluate application-side lifecycle mitigations if pin attempts are insufficient or skipped.
- As a **CI owner / test engineer**, I want evaluation anchored to reproducible proof surfaces (`tests/test_agent_dialog_settle_teardown_stress.py` with N=25 and `tests/test_agent_dialog_settle_e2e.py` without assertion regressions), ensuring native process stability without sacrificing existing test coverage.

## Definition of Done

This task (PYPOST-1209 / MITIGATE-1) is considered done when:

1. **Baseline State Documented**: The diagnosed baseline crash rate and execution environment established in PYPOST-1040 are documented in developer-facing notes.
2. **Success Threshold Defined**: An explicit, objective, and reviewable definition of a "materially reduced" crash rate is established for evaluation against the stress detector.
3. **Candidate Ordering & Stop-on-Success Rules Documented**: The candidate evaluation sequence (evaluating a dependency pin change in MITIGATE-2 before application-side changes in MITIGATE-3 unless justified otherwise) and the stop-on-success rules are clearly documented.
4. **Settlement Ownership Assigned**: The contract explicitly assigns detector marker (`xfail`) and developer documentation settlement ownership across all possible execution paths (MITIGATE-2 owns settlement if MITIGATE-3 is soft-skipped upon pin success; MITIGATE-3 owns settlement by default when it executes).
5. **Proof Surfaces Named**: The teardown stress detector (`tests/test_agent_dialog_settle_teardown_stress.py` with `STRESS_ITERATIONS = 25`) and the product dialog settle e2e test (`tests/test_agent_dialog_settle_e2e.py` with zero assertion regressions) are named as the mandatory proof surfaces for later children.
6. **Artifacts & Quality Gate**: `ai-tasks/PYPOST-1209/00-roadmap.md` and `10-requirements.md` exist and conform to repository Top-Down quality standards (`make verify-ai-tasks`).

## Task Description

### Problem

The PyPost agent dialog settle suite intermittently crashes with SIGSEGV or SIGBUS post-PASS during test process teardown. Diagnosis under PYPOST-1040 identified an upstream PySide6/shiboken6 `QWidgetItem` lifecycle defect triggered by pytest's `unraisableexception` plugin forcing cyclic garbage collection on `SettingsDialog`'s nested-layout widget tree.

Epic PYPOST-1115 was created to attempt mitigation. In PYPOST-1203, the epic was decomposed into three sequential child stories. As the first child (MITIGATE-1), PYPOST-1209 must define the shared evaluation framework before technical changes are attempted in MITIGATE-2 or MITIGATE-3.

### Scope

- Document the diagnosed baseline crash rate and environment boundary from PYPOST-1040.
- Formulate the explicit, reviewable success threshold for declaring a crash rate "materially reduced".
- Formalize the candidate evaluation order: dependency pin candidate first (MITIGATE-2), followed by application-side lifecycle modifications (MITIGATE-3).
- Define stop-on-success rules, ensuring that soft-skipping MITIGATE-3 transfers the obligation of test marker and dev docs settlement to MITIGATE-2.
- Specify the two proof surfaces: the statistical stress detector (N=25 child processes) and the functional e2e test suite.
- Provide developer-facing documentation/notes containing this evaluation contract.

### Out of Scope

- Implementing any dependency pin changes (owned by MITIGATE-2 / PYPOST-1210).
- Implementing any application-side cycle-breaking or lifecycle modifications (owned by MITIGATE-3 / PYPOST-1211).
- Re-diagnosing the crash mechanism or modifying the existing stress harness (PYPOST-1040 is closed).
- Sibling debt items such as duration-report xfail labeling (PYPOST-1116) or general GUI batch instability (PYPOST-1070).
- Altering production application code in `pypost/`.

### Functional Requirements

- **FR1 (Diagnosed Baseline Specification)**: The contract must explicitly state the diagnosed baseline crash rate of 32.5% (13 crashes out of 40 runs) observed on the supported reference environment: Linux (kernel 6.8 / Debian container), Python 3.13.5, PySide6-shiboken6 6.11.1, running offscreen (`QT_QPA_PLATFORM=offscreen`).
- **FR2 (Quantitative Success Threshold)**: The contract must state an explicit, reviewable criterion for a "materially reduced" crash rate:
  - Full mitigation success on the stress detector (`N=25` isolated child runs) is defined as achieving zero crashes (0/25 crashes, 0% crash rate).
  - An outcome is considered a partial / insufficient improvement if crashes still occur at a rate where `P(>=1 crash in 25 runs)` remains high or shows no statistically significant divergence from the 32.5% baseline.
- **FR3 (Candidate Evaluation Sequence)**: The contract must formalize the order of candidate evaluations:
  1. *Candidate 1 (MITIGATE-2)*: Dependency pin evaluation — assess newer/alternate PySide6/shiboken6 patch versions against the stress harness.
  2. *Candidate 2 (MITIGATE-3)*: Application-side mitigations — break reference cycles in `SettingsDialog` and/or introduce deliberate post-shutdown garbage collection in `AgentAppSession`.
- **FR4 (Stop-on-Success Protocol & Settlement Ownership)**:
  - If Candidate 1 (MITIGATE-2) satisfies the success threshold (zero crashes on N=25 stress detector and green e2e assertions), Candidate 2 (MITIGATE-3) may be soft-skipped with recorded evidence.
  - In the event of a soft-skip of MITIGATE-3, MITIGATE-2 **must** own the final settlement of the stress detector marker (`pytest.mark.xfail`) and developer documentation.
  - If Candidate 1 does not achieve epic success, MITIGATE-3 executes and serves as the default owner for marker and documentation settlement upon evaluating application-side candidates.
  - Settlement must never be left unassigned or orphaned regardless of which candidate succeeds or if all candidates are exhausted.
- **FR5 (Proof Surfaces Specification)**: The contract must designate and document the two required proof surfaces:
  - *Stability / Detection Surface*: `tests/test_agent_dialog_settle_teardown_stress.py` with `STRESS_ITERATIONS = 25` (providing >99.99% statistical detection power against the 32.5% baseline).
  - *Functional Preservation Surface*: `tests/test_agent_dialog_settle_e2e.py` (all functional assertions and logging contracts must remain green with no regressions).
- **FR6 (Developer Documentation Integration)**: The contract, baseline facts, and rules must be recorded in developer documentation for consumption by child tasks and maintainers.

### Non-Functional Requirements

- **NFR-1 (Clarity & Objectivity)**: All thresholds, ordering constraints, and stop conditions must be expressed quantitatively and unambiguously, allowing automated or human reviewers to evaluate outcomes without subjective interpretation.
- **NFR-2 (Traceability)**: All baseline figures, environment details, and candidate descriptions must trace directly to PYPOST-1040 diagnostic data and PYPOST-1203 architectural decisions.
- **NFR-3 (Orphan Prevention)**: The contract must guarantee that every possible path through MITIGATE-2 and MITIGATE-3 has a deterministically assigned owner for test marker (`xfail`) and documentation settlement.
- **NFR-4 (Zero Runtime Footprint)**: As a requirements and evaluation specification, this artifact and its accompanying developer notes introduce zero modifications to application runtime logic.

### Constraints and Assumptions

- The root cause established in PYPOST-1040 (upstream Shiboken `QWidgetItem` lifecycle bug under forced cyclic GC) is accepted as true and is not subject to re-investigation.
- The stress detector (`tests/test_agent_dialog_settle_teardown_stress.py`) remains marked `slow` (opt-in via `make test-slow` or direct invocation) to preserve fast default test runs.
- All repository validation and artifact integrity checks must be executed via `make verify-ai-tasks` and other `make` targets.

### Main Entities (Business & Evaluation Domain)

| Entity | Description / Role |
| --- | --- |
| **Mitigation Evaluation Contract** | The formal specification governing baseline facts, success thresholds, trial ordering, and settlement ownership for epic PYPOST-1115. |
| **Baseline Benchmark** | The reference crash rate (32.5%, 13/40) on the reference platform (Linux / Python 3.13 / PySide6 6.11.1 offscreen) established in PYPOST-1040. |
| **Success Threshold** | The objective standard (0/25 crashes on the stress detector with green e2e assertions) required to declare a mitigation candidate successful. |
| **Mitigation Candidates** | The sequence of attempted solutions: Dependency Pin (MITIGATE-2) followed by Application-Side Lifecycle Changes (MITIGATE-3). |
| **Stop-on-Success Rule** | The rule permitting the bypass of subsequent candidates when an earlier candidate meets the success threshold, conditioned on transferred settlement ownership. |
| **Settlement Ownership** | The explicit assignment of responsibility for updating the stress test's `xfail` marker and developer documentation (owned by MITIGATE-2 on pin-success skip, or MITIGATE-3 by default). |
| **Proof Surfaces** | The dual validation test suites: `tests/test_agent_dialog_settle_teardown_stress.py` (statistical crash detection) and `tests/test_agent_dialog_settle_e2e.py` (functional integrity). |

## Q&A

- **Q: Why must the evaluation contract be documented in a separate story before attempting mitigations?**
  - A: Separating the contract into MITIGATE-1 (PYPOST-1209) establishes an objective, reviewable standard before any code or dependency modifications occur. This prevents moving goalposts, ambiguous success claims, and confusion over which story is responsible for test marker updates.
- **Q: Why is dependency pin mitigation evaluated before application-side changes?**
  - A: A dependency pin change represents the least invasive and cleanest solution for an upstream binding defect. If an upstream patch resolves the defect cleanly without code changes, application-side workarounds can be avoided entirely.
- **Q: What happens if MITIGATE-2 (pin attempt) succeeds?**
  - A: Per the stop-on-success rule, MITIGATE-3 may be soft-skipped. However, MITIGATE-2 inherits the responsibility to update the detector's `xfail` marker and developer documentation so that settlement is not orphaned.
- **Q: What happens if MITIGATE-2 is inconclusive or fails?**
  - A: MITIGATE-2 records the outcome against the baseline, leaves the detector marker unchanged, and hands off execution to MITIGATE-3, which then attempts application-side candidates and settles the final outcome.
- **Q: Why is N=25 chosen for the stress detector?**
  - A: With a baseline crash probability of ~32.5% per run, 25 independent child runs provide `1 - (1 - 0.325)^25 ≈ 99.99%` statistical power to detect the crash if the defect remains active.
- **Q: Does this task implement or change any tests or product code?**
  - A: No. This task documents the evaluation contract, baseline figures, and developer guidance only. Product and test modifications are reserved for MITIGATE-2 and MITIGATE-3.

## References

- [PYPOST-1209](https://pypost.atlassian.net/browse/PYPOST-1209) — this task (MITIGATE-1)
- [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115) — parent epic (mitigate QWidgetItem GC-teardown crash)
- [PYPOST-1203](https://pypost.atlassian.net/browse/PYPOST-1203) — epic decomposition story
- [PYPOST-1040](https://pypost.atlassian.net/browse/PYPOST-1040) — diagnostic investigation of the teardown crash
- [PYPOST-1210](https://pypost.atlassian.net/browse/PYPOST-1210) — MITIGATE-2 (pin attempt)
- [PYPOST-1211](https://pypost.atlassian.net/browse/PYPOST-1211) — MITIGATE-3 (app-side attempt + settlement)
- `doc/dev/agent_dialog_settle.md` — developer documentation for dialog settle and teardown stress
- `tests/test_agent_dialog_settle_teardown_stress.py` — teardown stress detector
- `tests/test_agent_dialog_settle_e2e.py` — product dialog settle e2e suite
- `ai-tasks/PYPOST-1203/10-requirements.md` — decomposition requirements
- `ai-tasks/PYPOST-1203/20-architecture.md` — decomposition workflow architecture
- `ai-tasks/PYPOST-1040/20-architecture.md` — root cause investigation and baseline empirical evidence
