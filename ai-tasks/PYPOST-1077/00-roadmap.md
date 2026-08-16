# Roadmap: PYPOST-1077

## Task Metadata

- **Implementation language**: Python
- **Branch name**: `fix/PYPOST-1077-restore-test-contracts` (reference only; not switched)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1077/00-roadmap.md` — task progress journal and
    implementation language recorded.
  - `ai-tasks/PYPOST-1077/10-requirements.md` — business and functional
    requirements for preserving four established application contracts.
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1077/20-architecture.md` — evidence-based recovery plan
    for the four established contract checks and their Step 3 red repros.
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_pypost_1077_verification_artifacts.py` — local red artifact-contract
    checks for the dialog audit, function catalog expectation, Jira smoke declaration and
    invocation, and deferred environment presenter seam.
  - `make test PYTEST_ARGS=tests/test_pypost_1077_verification_artifacts.py` — red as
    intended: four deterministic artifact-drift failures; no import, fixture, transport, or
    live-service failure.
- [x] **STEP 4: Development**
  - [x] Reconciled the PYPOST-374 dialog audit with the eight-module, 1,030-LOC discovery,
    including the `mcp_servers_dialog.py` assessment and full testability inventory.
  - [x] Restored strict catalog, Jira board-pagination, and encrypted-startup test contracts;
    `tests/test_pypost_1077_verification_artifacts.py` is green.
  - [x] `make test PYTEST_ARGS='tests/test_pypost_1077_verification_artifacts.py
    tests/test_function_registry.py tests/test_jira_mcp_live_smoke.py
    tests/test_main_window_encrypted_startup.py -q'` — 24 passed, 1 deselected.
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1077/50-observability.md` — N/A assessment: PYPOST-1077
    restores verification artifacts and documentation only; it changes no production execution
    path that could emit task-specific logs or metrics.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1077/60-tech-debt.md` — records the intentional AST-artifact
    validation coupling, report-maintenance scope, complete timeout coverage, and pre-existing
    validation blockers outside this task's changed paths.
- [x] **STEP 8: Dev Docs**
  - `doc/dev/verification_artifact_contracts.md` — developer guide to the four restored
    verification-artifact contracts, focused offline validation, and drift troubleshooting.
  - `doc/dev/README.md` — links the guide from the testing and quality index.
- [x] **COMMIT: Commit Changes**
  - `test(contracts): PYPOST-1077 restore verification contracts` (see Git history)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1077/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1077/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1077/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1077/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1077/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID)
