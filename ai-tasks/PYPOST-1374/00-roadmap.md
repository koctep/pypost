# Roadmap: PYPOST-1374

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Create `ai-tasks/PYPOST-1374/00-roadmap.md` and `ai-tasks/PYPOST-1374/10-requirements.md`
  - [x] Gather and document business goals, functional requirements (FR-1 through FR-5), non-functional requirements, constraints, entities, and user stories
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Research `_McpServerEditor` lifecycle, overlay persistence, and wizard contracts
  - [x] Design component architecture, class relationships, and sequence flow
  - [x] Specify method contracts: `_on_configure_variables_clicked()`, `_sync_wizard_results_to_overlay()`, `_update_configure_variables_button_state()`
  - [x] Register widget ID `MCP_SERVER_CONFIGURE_VARIABLES_BUTTON`
  - [x] Formulate Step 3 automated failing repro test plan in `tests/test_mcp_servers_dialog_variable_wizard_repro.py`
  - [x] Document architecture in `ai-tasks/PYPOST-1374/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] Author automated red repro test in `tests/test_mcp_servers_dialog_variable_wizard_repro.py`
  - [x] Run failing test suite and confirm failure reason
  - [x] Verify repository integrity with make verify-ai-tasks and make lint
- [x] **STEP 4: Development**
  - [x] Register widget ID `MCP_SERVER_CONFIGURE_VARIABLES_BUTTON` in `pypost/ui/widget_ids.py`
  - [x] Implement configure variables button (`_ConfigureVariablesButton`) and layout embedding in `_McpServerEditor`
  - [x] Implement `_update_configure_variables_button_state` visibility and enablement management
  - [x] Implement `_on_configure_variables_clicked`, `_create_variable_wizard`, and `_launch_variable_wizard`
  - [x] Implement `_sync_wizard_results_to_overlay` for overlay and inline field synchronization
  - [x] Run repro test suite to confirm green transition (6/6 passing in `tests/test_mcp_servers_dialog_variable_wizard_repro.py`)
  - [x] Run regression test suites (`test_mcp_servers_dialog.py`, `test_variable_setup_wizard_repro.py`, `test_dialogs_audit.py`) and quality gates (`make lint`, `make typecheck`, `make verify-ai-tasks`)
- [x] **STEP 5: Code Cleanup**
  - [x] Static analysis, linting, formatting, and typing validation
  - [x] Dead code, unused imports, docstrings, and test timeout checks
  - [x] Document code cleanup in `ai-tasks/PYPOST-1374/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Identify UI runtime metrics and operational logging events for wizard launch, acceptance, and cancellation
  - [x] Enforce strict sensitive field masking rules preventing credential leakage in telemetry and logs
  - [x] Specify downstream observability contracts with Layer 4 (PYPOST-1375)
  - [x] Document process observability, Jira traceability, worklogs, and quality gate metrics
  - [x] Document observability implementation in `ai-tasks/PYPOST-1374/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze shortcuts taken, code quality issues, missing tests, and performance concerns
  - [x] Identify follow-up tasks (PYPOST-1375)
  - [x] Draft `ai-tasks/PYPOST-1374/60-tech-debt.md`
  - [x] Await review and approval (orchestrator marks [x] after review PASS)
- [x] **STEP 8: Dev Docs**
  - [x] Update `doc/dev/mcp_server_registry.md` with `VariableSetupWizardDialog` editor integration details
  - [x] Document configure variables button (`MCP_SERVER_CONFIGURE_VARIABLES_BUTTON`), visibility/enablement lifecycle
  - [x] Document wizard pre-population, modal acceptance/synchronization, and cancellation semantics
  - [x] Document headless test seams (`_create_variable_wizard`, `_launch_variable_wizard`)
  - [x] Create `ai-tasks/PYPOST-1374/70-dev-docs.md` recording documentation decisions and traceability
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1374/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1374/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test: `tests/test_mcp_servers_dialog_variable_wizard_repro.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1374/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1374/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1374/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_server_registry.md`
- `ai-tasks/PYPOST-1374/70-dev-docs.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
