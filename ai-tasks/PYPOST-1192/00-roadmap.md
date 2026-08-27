# Roadmap: PYPOST-1192

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1192/10-requirements.md`
  - Language: Python
  - Business goal: bound orchestrator wait for each worker so hung workers
    cannot stall `make test` / CI indefinitely
  - Default wait bound TIMEOUT = 30 seconds; configurable; timeout →
    failed/timed-out worker with clear structured log; automated tests;
    update runner contract docs if needed
  - Related: PYPOST-1149 orchestrator; debt item in PYPOST-1153 (per-file
    wall-clock timeout only — other 1153 items out of scope)
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1192/20-architecture.md`
  - Bound wait via `subprocess.run(..., timeout=worker_timeout)` in
    `SubprocessTestExecutor` (not `future.result` alone — that cannot free
    hung pool threads)
  - Config: `--worker-timeout` / env `WORKER_TIMEOUT` / default 30; avoid
    clashing with pytest-timeout `--timeout`
  - New `TestStatus.TIMED_OUT`; structured `worker_timeout` log; counts as
    run failure
  - Failing-repro plan: short TIMEOUT + hang fixture/mock in
    `tests/test_run_parallel_tests.py` (Step 3)
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_run_parallel_tests.py::test_hung_worker_under_timeout_yields_timed_out`
  - Harness: inject `config.worker_timeout` post-construct; assert status `"timed_out"`
    (not `RunnerConfig(worker_timeout=...)` / `TestStatus.TIMED_OUT` — those raise before
    the intended red path)
- [x] **STEP 4: Development**
  - [x] Iteration 1: Added `TestStatus.TIMED_OUT`, `RunnerConfig.worker_timeout`
    (default 30), `get_worker_timeout` (CLI → `WORKER_TIMEOUT` → 30),
    `--worker-timeout` CLI parsing, `subprocess.run(..., timeout=...)` with
    `TimeoutExpired` → timed-out `TestResult` + `worker_timeout` log; timed-out
    files count as failures in summary/FAILURES
  - [x] Iteration 2: Wired `WORKER_TIMEOUT ?= 120` into Makefile `test` /
    `test-cov` (`--worker-timeout`) so suite files (makefile smoke ~64–87s) are
    not killed by the script's product default of 30s; hung-worker repro green
  - [x] Iteration 3: Triaged suite reds at base `18a4d9d1` — filed
    PYPOST-1193/1194/1195/1196; noted websocket hang TIMED_OUT under PYPOST-1181;
    recorded in `60-tech-debt.md`. Step 3 repro remains green.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1192/40-code-cleanup.md`
  - Cleaned hung-worker test: constructor `worker_timeout`, `TestStatus.TIMED_OUT`,
    removed Step 3 red-repro comments
  - `make lint` OK; focused `tests/test_run_parallel_tests.py` green
  - `make analyze` N/A (no target); `make typecheck` red on unrelated baseline
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1192/50-observability.md`
  - Documented Step 4 timeout signals: WARNING `worker_timeout`, INFO
    `test_file_completed` with `status=timed_out`, ERROR `test_file_timed_out`
  - Validated via hung-worker caplog assertions; no new log sites required
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1192/60-tech-debt.md` (refined from Step 4 triage)
  - Debt: process-group orphans deferred; Make `WORKER_TIMEOUT?=120` vs script
    default 30; `parallel_test_run_started` omits `worker_timeout`; missing
    `get_worker_timeout` / makefile contract tests; coverage combine still
    unbounded (pre-existing)
  - Pre-existing filed: PYPOST-1193/1194/1195/1196; hang → PYPOST-1181
  - Timeout markers on this task's tests: no blocker
- [x] **STEP 8: Dev Docs**
  - `doc/dev/parallel_test_runner.md` — document `--worker-timeout` /
    `WORKER_TIMEOUT`, script default 30 vs Make `WORKER_TIMEOUT ?= 120`,
    `TIMED_OUT` / `worker_timeout` log, and related runner contract
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1192/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1192/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1192/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1192/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1192/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/parallel_test_runner.md` — `--worker-timeout` / `WORKER_TIMEOUT`,
  dual defaults (script 30 vs Make 120), `TIMED_OUT` / `worker_timeout` log,
  JSON `timed_out`, Makefile wiring

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
