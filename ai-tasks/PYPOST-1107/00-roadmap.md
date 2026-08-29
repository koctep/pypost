# Roadmap: PYPOST-1107

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1107/00-roadmap.md` created with task metadata
  - [x] `ai-tasks/PYPOST-1107/10-requirements.md` created detailing goals, user stories, requirements, and DoD
  - Step 1 acceptance gate passed (review verdict PASS)
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1107/20-architecture.md` created with research, implementation plan, failing repro strategy, architecture diagram, and module boundaries
  - Step 2 acceptance gate passed (review verdict PASS)
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_env_presenter_mcp_controller_seam.py` created asserting removal of `set_mcp_server_controller`
  - Step 3 acceptance gate passed (review verdict PASS)
- [x] **STEP 4: Development**
  - [x] Removed `set_mcp_server_controller` delegating shim and unused `McpServerController` import from `pypost/ui/presenters/env_presenter.py`
  - [x] Updated `MainWindow` initialization in `pypost/ui/main_window.py` to directly configure `self.mcp_controls.set_server_controller(self.mcp_controller)`
  - [x] Removed `set_mcp_server_controller` from `_DeferredEnvPresenter` test double in `tests/test_main_window_encrypted_startup.py`
  - [x] Updated AST contract assertions in `tests/test_pypost_1077_verification_artifacts.py` to verify `mcp_controls` double initialization and absence of `set_mcp_server_controller`
  - [x] Updated developer documentation in `doc/dev/presenter_architecture.md`, `doc/dev/mcp_integration.md`, and `doc/dev/verification_artifact_contracts.md`
  - [x] Verified targeted tests and quality gates pass via `make test` and `make lint`
  - Step 4 acceptance gate passed (review verdict PASS)
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1107/40-code-cleanup.md` created documenting linter fixes, formatting, cleanup, and validation results
  - Step 5 acceptance gate passed (review verdict PASS)
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1107/50-observability.md` created documenting logging review, telemetry preservation, and validation results
  - Step 6 acceptance gate passed (review verdict PASS)
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1107/60-tech-debt.md` created with shortcuts, code quality issues, missing tests, performance concerns, and tracked pre-existing base issues
  - Step 7 acceptance gate passed (review verdict PASS)
- [x] **STEP 8: Dev Docs**
  - [x] Updated developer documentation in `doc/dev/presenter_architecture.md`, `doc/dev/mcp_integration.md`, and `doc/dev/verification_artifact_contracts.md`
  - Step 8 acceptance gate passed (review verdict PASS)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1107/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1107/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1107/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1107/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1107/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
