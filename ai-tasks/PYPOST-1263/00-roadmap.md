# Roadmap: PYPOST-1263

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Independent requirements review passed; orchestrator accepted Step 1.
- [x] **STEP 2: High-Level Architecture Design**
  - Independent architecture review passed; orchestrator accepted Step 2.
  - Designed per-thread CPU-work gating at the existing 100ms budget with wall diagnostics.
  - Defined deterministic clock observations around the real benchmark and planner call.
    Architecture prepared for independent review.
- [x] **STEP 3: Failing Repro Test**
  - Independent re-review reproduced all four intended failures; orchestrator accepted Step 3.
  - Added deterministic actual-benchmark/real-planner regressions in
    `tests/test_collection_import_profile_clock.py`; benchmark implementation unchanged.
  - Ran `make test WORKERS=1` with
    `PYTEST_ARGS='tests/test_collection_import_profile_clock.py'`: three intended failures,
    Make exit 2. No setup/import failures; the real planner ran with the preserved workload.
  - Exact failing nodes use prefix `tests/test_collection_import_profile_clock.py::`,
    test name `test_planner_benchmark_distinguishes_cpu_work_from_wall_delay`, and IDs
    `[external-descheduling]`, `[excess-planner-work]`, `[strict-cpu-boundary]`.
  - Descheduling case fails at the existing 500ms wall rejection despite supplied 40ms CPU.
    Slow/boundary cases fail because the existing rejection lacks required CPU attribution.
    All three expose the wall-only metric; the benchmark implementation remains untouched.
  - Tests assert single real planner invocation, fixture scale/conflicts/decision types,
    two readings per clock, and interval placement. Ten-second module timeout is explicit.
    Independent review pending.
  - Step 3 review correction: added delegating fixture/conflict observers and asserted both
    fixtures and initial conflict discovery finish before the first read of either clock.
    Planner spy uses the saved real conflict finder so setup-event counts stay exact.
  - Parameterized wall observations and added `[synthetic-low-wall-high-cpu]` to the same
    node prefix/test name above: 10ms synthetic wall versus 150ms CPU must reject, proving
    budget enforcement independently of a high wall diagnostic value.
  - Repeated the same targeted Make command: four intended failures, Make exit 2. New
    low-wall/high-CPU case fails with `DID NOT RAISE`; original cases remain red at wall-only
    rejection/CPU diagnostic mismatch. Descheduling scenario now supplies 20ms CPU.
    Existing benchmark remains unchanged; Step 3 re-review pending.
- [x] **STEP 4: Development**
  - Independent implementation review passed; orchestrator accepted Step 4.
  - Implemented strict 100ms current-thread CPU-work gate around the existing planner call;
    wall elapsed time remains diagnostic context. Preserved workload and functional checks.
  - Green: `make test WORKERS=1` with `PYTEST_ARGS` selecting
    `tests/test_collection_import_profile_clock.py` and
    `tests/test_collection_import_profile.py`: both modules passed in 2.65 seconds.
    All four reviewed reds and the real-clock benchmark pass.
  - `make lint` passed; `make typecheck` passed against the unchanged 181-error baseline.
    No production changes or other profile-test edits. Independent Step 4 review pending.
- [x] **STEP 5: Code Cleanup**
  - Independent cleanup review passed; orchestrator accepted Step 5.
  - Reviewed both changed test files for formatting, used imports, clock scope, and timeouts.
    No further code edits needed; cleanup report prepared for independent review.
  - `make lint` and `make verify-ai-tasks` passed (394 completed tasks; two legacy gaps).
- [x] **STEP 6: Observability**
  - Independent observability re-review passed; orchestrator accepted Step 6.
  - `ai-tasks/PYPOST-1263/50-observability.md`: test-only change, so no production logs or
    metrics added (AC-8). Existing `collection_import_plan_created` INFO log is unchanged.
  - Diagnostic surface is the benchmark assertion message, which reports thread CPU ms and
    wall elapsed ms. The clock regression tests check it. Independent review pending.
  - `make verify-ai-tasks` (2026-10-08): passed, exit 0. Printed "ai-tasks artifacts baseline
    OK (394 completed tasks; 2 grandfathered legacy gaps)".
- [x] **STEP 7: Technical Debt Analysis**
  - Independent tech-debt review passed; orchestrator accepted Step 7.
  - `ai-tasks/PYPOST-1263/60-tech-debt.md`: no shortcuts in scope; CPU gate is not a
    wall-latency guarantee and assumes a synchronous planner (accepted, documented).
  - Timeout-marker BLOCKER check passed: profile module `timeout(60)`, clock module `timeout(10)`.
  - Follow-ups (Jira: TBD): Medium — CPU gate for remaining wall-threshold tests in the
    profile module (`conflict_matrix_profile` 50ms, `apply_imported_collections_performance`
    500ms); Low — review Qt event-loop latency thresholds (PYPOST-1242 burst tests, websocket
    offscreen tick); Lowest — optional CPU/wall fields on `collection_import_plan_created`.
  - Minor style notes (missing `-> None`, clock-module import grouping) recorded, no ticket.
  - `make verify-ai-tasks` (2026-10-08): passed, exit 0. Printed "ai-tasks artifacts baseline
    OK (394 completed tasks; 2 grandfathered legacy gaps)". Independent review pending.
- [x] **STEP 8: Dev Docs**
  - Independent dev-docs review passed; orchestrator accepted Step 8.
  - Started: updating `doc/dev/collection_import.md` for the CPU-work planner benchmark.
  - `doc/dev/collection_import.md`: PYPOST-1062 overview now points to the new subsection
    "Planner CPU-work benchmark (PYPOST-1263)". It covers the thread-CPU gate, why it changed,
    the planner assumption, how to read the failure message, the clock regression module, the
    Make command, and the wall gates left to PYPOST-1318 and PYPOST-1317. Also added one
    Troubleshooting entry. No new doc file, so the doc index is unchanged.
  - `make lint` (2026-10-08): passed, exit 0 (flake8; Markdown lint OK, 16 files; link check
    OK, 18 files). Doc lint covers `doc/user/` and READMEs, not `doc/dev/`.
  - `make verify-ai-tasks` (2026-10-08): passed, exit 0. Printed "ai-tasks artifacts baseline
    OK (394 completed tasks; 2 grandfathered legacy gaps)". Independent review pending.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1263/10-requirements.md`
- Captured contention reliability, preserved workload/functionality, and slowdown detection.
- Step 1 prepared for independent review; no test or production changes made.

### STEP 2: Architecture

- `ai-tasks/PYPOST-1263/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1263/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1263/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1263/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
