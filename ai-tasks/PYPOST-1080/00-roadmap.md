# Roadmap: PYPOST-1080

## Task Metadata

- **Implementation language**: Python
- **Branch name**: test/PYPOST-1080-mcp-server-controller-presenter-tests

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Document requirements for dedicated test coverage of `pypost/ui/mcp_server_controller.py` and `pypost/ui/presenters/mcp_controls_presenter.py`
  - [x] Define acceptance criteria for uncovering `mcp_server_activity` KeyError branch, create/update persist paths, and `_open_mcp_servers` with dialog logging
  - [x] Produce requirements artifact `ai-tasks/PYPOST-1080/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Design test suite architecture for `test_mcp_server_controller.py` and `test_mcp_controls_presenter.py`
  - [x] Specify test scenarios, mock structures, Qt fixtures, and log capture assertions
  - [x] Create architecture artifact `ai-tasks/PYPOST-1080/20-architecture.md`
- [x] **STEP 3: Failing Repro Test / Verification Test**
  - [x] Create minimal test skeletons demonstrating missing test assertions
  - [x] Confirm execution and test suite wiring
- [x] **STEP 4: Development**
  - [x] Implement comprehensive test suites in `tests/test_mcp_server_controller.py` and `tests/test_mcp_controls_presenter.py`
  - [x] Ensure all tests pass GREEN with explicit timeout markers
- [x] **STEP 5: Code Cleanup**
  - [x] Run `make lint`
  - [x] Produce `ai-tasks/PYPOST-1080/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Document test verification of logs and error tracking
  - [x] Produce `ai-tasks/PYPOST-1080/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze technical debt and test coverage outcomes
  - [x] Produce `ai-tasks/PYPOST-1080/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Update testing developer documentation in `doc/dev/`
  - [x] Produce `ai-tasks/PYPOST-1080/70-dev-docs.md`
- [x] **COMMIT: Commit Changes**
  - Commit: `eb4b4d99` test(ui): add dedicated test modules for mcp server controller and presenter (PYPOST-1080)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

## Artifacts

### STEP 1: Requirements
- `ai-tasks/PYPOST-1080/10-requirements.md`

### STEP 2: Architecture
- `ai-tasks/PYPOST-1080/20-architecture.md`

### STEP 3: Failing Repro / Verification Test
- `tests/test_mcp_server_controller.py`
- `tests/test_mcp_controls_presenter.py`

### STEP 4: Development
- `tests/test_mcp_server_controller.py`
- `tests/test_mcp_controls_presenter.py`

### STEP 5: Code Cleanup
- `ai-tasks/PYPOST-1080/40-code-cleanup.md`

### STEP 6: Observability
- `ai-tasks/PYPOST-1080/50-observability.md`

### STEP 7: Technical Debt
- `ai-tasks/PYPOST-1080/60-tech-debt.md`

### STEP 8: Dev Docs
- `doc/dev/testing.md`
- `ai-tasks/PYPOST-1080/70-dev-docs.md`

### COMMIT
- `eb4b4d99` test(ui): add dedicated test modules for mcp server controller and presenter (PYPOST-1080)
