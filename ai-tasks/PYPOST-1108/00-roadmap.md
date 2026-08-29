# Roadmap: PYPOST-1108

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1108/00-roadmap.md`
  - `ai-tasks/PYPOST-1108/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1108/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_env_mcp_signals_decoupled.py`
- [x] **STEP 4: Development**
  - [x] Iteration 1: Decouple EnvPresenter and McpControlsPresenter with domain Qt signals
    - Defined `environment_selected`, `environment_updated`, and `environment_manager_closed` Qt signals in `EnvPresenter`.
    - Removed direct operational calls from `EnvPresenter` to `McpControlsPresenter`.
    - Implemented `on_environment_manager_closed()` and internalized environment tracking in `McpControlsPresenter`.
    - Connected domain signals in `pypost/ui/main_window_signals.py`.
    - All tests in `tests/test_env_mcp_signals_decoupled.py`, `tests/test_env_presenter.py`, `tests/test_mcp_controls_presenter.py`, and `tests/test_main_window_signals.py` pass.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1108/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1108/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1108/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - `doc/dev/environment_mcp_signals.md`
  - `doc/dev/environments.md`
  - `doc/dev/presenter_architecture.md`
  - `doc/dev/README.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1108/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1108/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1108/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1108/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1108/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/environment_mcp_signals.md`
- `doc/dev/environments.md`
- `doc/dev/presenter_architecture.md`
- `doc/dev/README.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
