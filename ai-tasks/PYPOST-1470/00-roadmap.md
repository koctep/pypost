# Roadmap: PYPOST-1470 — Process-mode 10x stress parity + Windows stop CI

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Documented business goals, user stories (Operator, Developer, CI maintainer), Definition of
    Done, 10x process stress parity, and Windows stop escalation CI in
    `ai-tasks/PYPOST-1470/10-requirements.md`.
  - Implementation language confirmed as Python in Task Metadata.
- [x] **STEP 2: High-Level Architecture Design**
  - Designed 10x process stress parity architecture and test suite layout in
    `ai-tasks/PYPOST-1470/20-architecture.md`.
  - Detailed `CollectionVariablesIntegrationHarness` extension for `execution_mode="process"`.
  - Analyzed Windows `TerminateProcess` semantics vs POSIX signals and supervisor escalation.
  - Designed `windows-process-stop` CI job on `windows-latest` for `.github/workflows/test.yml`.
  - Formulated Step 3 red failing repro plan targeting `tests/test_mcp_process_stress_10x.py`.
- [x] **STEP 3: Failing Repro Test**
  - Created red repro test suite in `tests/test_mcp_process_stress_10x.py` covering 5 acceptance
    scenarios (barrier startup, namespace isolation, TCP RST resilience, concurrent teardown,
    and Windows stop escalation).
  - Verified all 5 tests fail with expected missing capability:
    `TypeError: CollectionVariablesIntegrationHarness.__init__() got an unexpected keyword`
    `argument 'execution_mode'`.
  - Saved red test execution log to `/tmp/PYPOST-1470-step3-red.log`.
- [x] **STEP 4: Development**
  - Extended `ServerRegistryFixtureMixin` and `CollectionVariablesIntegrationHarness` in
    `tests/helpers/collection_integration_harness.py` with `execution_mode: Literal["thread",
    "process"] = "thread"`.
  - Added support for both thread managers and process runners in `start_standalone_server` when
    polling `is_listening` / `last_start_error`.
  - Added safe runner cleanup in `teardown()` ensuring active process runners are cleanly stopped.
  - Added dedicated `windows-process-stop` job on `windows-latest` to `.github/workflows/test.yml`.
  - Drove all 5 tests in `tests/test_mcp_process_stress_10x.py` green; verified thread-mode stress
    and process isolation tests continue to pass.
- [x] **STEP 5: Code Cleanup**
  - Ran `make -o lint-tests lint` and `make typecheck` (mypy baseline gate); passed cleanly.
  - Verified no unused imports, dead code, or debug prints in harness and stress test suite.
  - Verified strict <= 100 character line length across all modified and artifact files.
  - Documented cleanup results in `ai-tasks/PYPOST-1470/40-code-cleanup.md`.
- [x] **STEP 6: Observability**
  - Documented structured logging schemas for worker stop escalation (`mcp_worker_terminate`,
    `mcp_worker_kill`, exit codes, timeouts) in `ai-tasks/PYPOST-1470/50-observability.md`.
  - Documented secret safety guarantees (sanitization, no credentials in logs/memory dumps).
  - Documented Windows CI diagnostics and step summaries for `windows-process-stop` job.
  - Verified 10x process stress suite passing all 5 tests and quality gates clean.
- [x] **STEP 7: Technical Debt Analysis**
  - Documented technical debt analysis and shortcuts in `ai-tasks/PYPOST-1470/60-tech-debt.md`.
  - Triaged PYPOST-1509 as pre-existing non-blocker.
  - Formulated non-blocking operational follow-ups (Windows runner tuning, Win32 job objects).
  - Independent Blocker Reviewer returned `SAFE TO CLOSE (PASS)` with zero blocking debt items.
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/mcp_process_isolation.md` with 10x process stress suite architecture,
    Win32 `TerminateProcess` vs POSIX signals comparison, `windows-process-stop` CI job,
    troubleshooting rows, test commands, and 5-point acceptance criteria test coverage mapping.
  - Verified zero lines exceeding 100 characters across all 1,018 lines.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1470/10-requirements.md`
  - 10x process barrier startup, concurrent isolation, abrupt disconnect RST, and port reclamation.
  - Cross-platform Windows stop escalation CI verification (TerminateProcess semantics).

### STEP 2: Architecture

- `ai-tasks/PYPOST-1470/20-architecture.md`
  - Research on thread-mode 10x baseline, process isolation, supervisor escalation, and Win32.
  - Harness extension specification for `execution_mode="process"`.
  - Layout of 10x process stress suite and cross-platform stop escalation tests.
  - Mermaid architecture diagram and sequence diagram for process-mode lifecycle.
  - Step 3 failing repro plan.

### STEP 3: Failing Repro

- `tests/test_mcp_process_stress_10x.py`
  - `test_mcp_process_10x_parallel_startup_barrier_synchronization`
  - `test_mcp_process_10x_variable_namespace_isolation_under_concurrent_load`
  - `test_mcp_process_10x_abrupt_client_disconnect_rst_resilience`
  - `test_mcp_process_10x_concurrent_teardown_and_socket_reclamation`
  - `test_mcp_process_windows_stop_escalation_simulate_terminate_to_kill`
- Red test execution log: `/tmp/PYPOST-1470-step3-red.log`

### STEP 4: Development

- `tests/helpers/collection_integration_harness.py`
  - Added `execution_mode` parameter to `ServerRegistryFixtureMixin` and
    `CollectionVariablesIntegrationHarness`.
  - Polling and teardown support for process runners.
- `.github/workflows/test.yml`
  - Added `windows-process-stop` CI job on `windows-latest` runner with offscreen Qt platform.
- `tests/test_mcp_process_stress_10x.py`
  - Full 10x process stress suite passing all 5 tests.

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1470/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1470/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1470/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
