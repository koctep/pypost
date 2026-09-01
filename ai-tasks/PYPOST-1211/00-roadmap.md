# Roadmap: PYPOST-1211

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Gather business goals and requirements from epic PYPOST-1115 / MITIGATE-1 / MITIGATE-2 context
  - [x] Define user stories, definition of done, functional and non-functional requirements
  - [x] Define domain entities, constraints, and business-level Q&A
  - [x] Create requirements document at `ai-tasks/PYPOST-1211/10-requirements.md`
  - [x] Review gate passed (PASS)
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Review root cause diagnosis from PYPOST-1040 and dependency evaluation findings from PYPOST-1210
  - [x] Design application-side mitigation candidates (layout cycle breaking and controlled GC/deferred deletion lifecycle)
  - [x] Define Step 3 red-repro execution protocol and Step 4 development & measurement workflows
  - [x] Model deterministic settlement state machine (Path B success vs Path C upstream exhaustion)
  - [x] Create architecture document at `ai-tasks/PYPOST-1211/20-architecture.md`
  - [x] Review gate passed (PASS)
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_dialog_settle_teardown_stress.py` (stress detector with intermittent crash repro / xfail under load) and `tests/test_agent_dialog_settle_e2e.py` (functional settle verification)
    - Functional settle suite verified 100% green: `make test-agent-e2e PYTEST_ARGS="tests/test_agent_dialog_settle_e2e.py -v"` (2 passed in 0.90s)
    - Teardown stress detector verified: `make test-agent-e2e PYTEST_ARGS="tests/test_agent_dialog_settle_teardown_stress.py -v -m slow"` (executes 25 child runs against unmitigated dialog layout teardown; marked `@pytest.mark.xfail(strict=False, reason="PYPOST-1040: intermittent QWidgetItem GC-teardown crash")`)
  - [x] Review gate passed (PASS)
- [x] **STEP 4: Development**
  - [x] Implement application-side cycle breaking in `SettingsDialog` (`cleanup()` hook) and post-dismiss deletion hardening in `MainWindow.open_settings()`
  - [x] Implement controlled garbage collection in `AgentAppSession.shutdown()`
  - [x] Measure empirical stability across $N=25$ runs on teardown stress detector (`0/25` crashes, 100% clean exit)
  - [x] Verify functional preservation on `tests/test_agent_dialog_settle_e2e.py` (100% green, 2 passed in ~0.9s)
  - [x] Settle epic PYPOST-1115 outcome under Path B: remove `xfail` from `tests/test_agent_dialog_settle_teardown_stress.py` and update `doc/dev/agent_dialog_settle.md`
  - [x] Review gate passed (PASS)
- [x] **STEP 5: Code Cleanup**
  - [x] Run static analysis and formatting checks (`make lint`, `make lint-docs`, `make check-docs-links`, `make verify-ai-tasks`, `make typecheck`)
  - [x] Verify e2e functional test suite (`make test-agent-e2e PYTEST_ARGS="tests/test_agent_dialog_settle_e2e.py -v"`)
  - [x] Create code cleanup artifact at `ai-tasks/PYPOST-1211/40-code-cleanup.md`
  - [x] Review gate passed (PASS)
- [x] **STEP 6: Observability**
  - [x] Analyze logging contracts and diagnostic visibility in stress detector and functional tests
  - [x] Document statistical metrics, crash rate elimination (0/25 crashes, 100% clean exit), and CI telemetry
  - [x] Create ai-tasks/PYPOST-1211/50-observability.md
  - [x] Review gate passed (PASS)
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze shortcuts, code quality, missing tests, and performance concerns
  - [x] Document Path B epic settlement and pre-existing failing test triage
  - [x] Create ai-tasks/PYPOST-1211/60-tech-debt.md
- [x] **STEP 8: Dev Docs**
  - [x] Document application-side reference cycle breaking (`SettingsDialog.cleanup()`), lifecycle `try ... finally` handling in `MainWindow.open_settings()`, and controlled GC in `AgentAppSession.shutdown()` in `doc/dev/agent_dialog_settle.md`
  - [x] Document empirical stability results across $N=25$ runs (0/25 crashes, 100% clean exits, complete elimination of 32.5% baseline)
  - [x] Document functional preservation on `tests/test_agent_dialog_settle_e2e.py` (100% green)
  - [x] Document final epic settlement: removal of `pytest.mark.xfail` from `tests/test_agent_dialog_settle_teardown_stress.py` and successful closure of epic PYPOST-1115 under Path B
  - [x] Validate documentation with `make lint-docs`, `make check-docs-links`, and `make verify-ai-tasks`
  - [x] Review gate passed (PASS)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1211/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1211/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_dialog_settle_teardown_stress.py` — Teardown stress detector (25 child subprocess runs under unmitigated layout teardown, marked `@pytest.mark.xfail(strict=False)`)
- `tests/test_agent_dialog_settle_e2e.py` — Functional dialog settle e2e suite (baseline 100% green)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1211/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1211/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1211/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/agent_dialog_settle.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
