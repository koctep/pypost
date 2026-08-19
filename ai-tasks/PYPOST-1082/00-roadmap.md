# Roadmap: PYPOST-1082

## Task Metadata

- **Implementation language**: Python
- **Branch name**: `refactoring/PYPOST-1082-retire-env-presenter-mcp-shims`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_env_presenter_mcp_shims_retired.py`
- [x] **STEP 4: Development**
  - [x] Update `EnvPresenter` docstring, add public `mcp_controls` property, and remove legacy delegating shims (`mcp_status_text`, `mcp_tools_button_text`, `mcp_activity_button_text`, `refresh_mcp_tools`)
  - [x] Expose `mcp_controls` attribute on `MainWindow` delegating to `env.mcp_controls`
  - [x] Rewire `collections_changed`, `requests_deleted`, and `request_saved` signals directly to `window.mcp_controls.refresh_tools` in `main_window_signals.py`
  - [x] Modernize unit and integration tests to invoke `p.mcp_controls` methods directly
  - [x] Verify green test suite and clean lint checks (`make lint`, `pytest`)
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
  - [x] Verify presenter logging levels (INFO, WARNING, ERROR, DEBUG) across `EnvPresenter` and `McpControlsPresenter`
  - [x] Verify signal routing observability for `mcp_controls.refresh_tools`
  - [x] Validate metrics tracking (`track_mcp_active_env_changed`, `track_variable_validation`)
  - [x] Create `ai-tasks/PYPOST-1082/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze codebase presenter separation, signal wiring, and remaining coupling
  - [x] Create `ai-tasks/PYPOST-1082/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
- [x] **COMMIT: Commit Changes**
  - Commit hash: `2b770ada` on `dev` — "refactoring(ui): PYPOST-1082 retire EnvPresenter MCP delegating shims"
  - Branch name (reference only, not switched): `refactoring/PYPOST-1082-retire-env-presenter-mcp-shims`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1082/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1082/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1082/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1082/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1082/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID)
