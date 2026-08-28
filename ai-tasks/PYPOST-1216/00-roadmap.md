# Roadmap: PYPOST-1216

## Task Metadata

- **Implementation language**: Python (diagnostic probes/traces) +
  Markdown (written root-cause diagnosis)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1216/10-requirements.md` drafted
  - Requirements, user stories, acceptance criteria, boundaries, entities,
    failure class criteria, and non-goals documented
  - Step 1 left in progress `[/]` pending acceptance gate review
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1216/20-architecture.md` drafted
  - Concurrency architecture & Mermaid sequence diagram constructed
  - Direct `apply_theme` vs `uvicorn` race evaluated and refuted;
    compound GIL/CPU contention confirmed
  - Failure class taxonomy established with explicit differentiation from
    PYPOST-1117 (large-batch segfault) and PYPOST-1115/1040 (dialog GC teardown)
  - Downstream FIX-1 (PYPOST-1217) stabilization recommendations and
    architectural constraints defined
  - Step 3 failing repro determined as N/A (diagnostic investigation only;
    no production modifications)
- [x] **STEP 3: Failing Repro Test**
  - `ai-tasks/PYPOST-1216/25-failing-repro.md` documented
  - N/A — diagnostic investigation only (no runtime behavioral change in this task;
    stabilization owned by FIX-1 / PYPOST-1217)
  - Zero modifications to production code in `pypost/` confirmed
- [x] **STEP 4: Development**
  - [x] Iteration 1: Delivered canonical root-cause diagnosis report
    (`ai-tasks/PYPOST-1216/30-diagnosis-report.md`) evaluating
    `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises`,
    refuting direct in-memory `apply_theme` vs `uvicorn` race, confirming
    compound GIL/CPU contention and Qt event loop starvation under multi-worker
    parallel execution, establishing failure class taxonomy, providing comparative
    differentiation from PYPOST-1117 and PYPOST-1115/1040, and defining downstream
    handoff specifications for FIX-1 (PYPOST-1217). Zero modifications to
    production code in `pypost/`.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1216/40-code-cleanup.md` created
  - Clean `make lint` verified (flake8, doc markdown lint, relative doc links)
  - Clean `make verify-ai-tasks` verified (302 tasks checked)
  - Zero modifications to production code in `pypost/` confirmed
  - Step 5 left in progress `[/]` pending acceptance gate review
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1216/50-observability.md` created
  - Structured logging analysis across `AgentAppSession`, `ui_wait`, and `MetricsServer`
  - Diagnostic metrics evaluated across single-node, single-file, concurrent subset,
    and full parallel suite profiles
  - Timeout hierarchy (test 60s, worker 120s, poll 10s/30s) and event loop polling latencies
    documented
  - Trace telemetry captured refuting direct `apply_theme` vs `uvicorn` race and confirming
    compound GIL/CPU contention
  - Downstream observability specifications established for FIX-1 (PYPOST-1217)
  - Zero modifications to production code in `pypost/` confirmed
  - Step 6 acceptance gate passed (review verdict PASS)
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1216/60-tech-debt.md` created
  - Analyzed shortcuts taken: pure diagnostic story without production modifications
    (FIX-1 owned by [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217))
  - Code quality verified: zero production code changed, clean markdown and artifact hygiene
  - Missing tests: verified explicit timeout markers across test suite per `do-testing` (no blocker)
  - Performance concerns: compound GIL/CPU contention under 8-worker parallel execution documented
  - Follow-up tasks documented: downstream stabilization (FIX-1 / PYPOST-1217) as NON-BLOCKER
  - Step 7 acceptance gate passed (review verdict PASS)
- [/] **STEP 8: Dev Docs**
  - Updated `doc/dev/testing.md` with comprehensive root-cause analysis for
    `test_live_collection_tree_missing_option_raises` parallel flake
  - Documented empirical refutation of the direct in-memory `apply_theme` vs
    `uvicorn` race hypothesis
  - Documented confirmed failure mechanism: compound GIL/CPU contention under
    multi-worker parallel execution starving main Qt GUI thread event loop pump
  - Documented failure class taxonomy (Classes 1-4) with explicit differentiation
    from PYPOST-1117 (large-batch segfault) and PYPOST-1115/1040 (dialog GC teardown)
  - Documented downstream stabilization architecture and handoff specifications for
    FIX-1 ([PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217))
  - Updated `doc/dev/gui_testing.md` troubleshooting table with diagnosis summary
    and cross-link to `doc/dev/testing.md`
  - Verified clean `make lint` and `make verify-ai-tasks`
  - Step 8 acceptance gate passed (review verdict PASS)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1216/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1216/20-architecture.md`

### STEP 3: Failing Repro

- `ai-tasks/PYPOST-1216/25-failing-repro.md` (N/A note and justification for diagnostic story)

### STEP 4: Development

- `ai-tasks/PYPOST-1216/30-diagnosis-report.md` (Canonical Root-Cause Diagnosis Report &
  Stabilization Specifications)

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1216/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1216/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1216/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md` (root-cause diagnosis, refutation, failure class taxonomy,
  and downstream stabilization specifications for FIX-1)
- `doc/dev/gui_testing.md` (troubleshooting table entry and cross-reference)

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
