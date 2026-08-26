# Roadmap: PYPOST-1171

## Task Metadata

- **Implementation language**: Python (PySide6 / pytest)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_mcp_client_migration.py::test_method_combo_excludes_mcp`
  - [x] `tests/test_mcp_client_migration.py::test_legacy_mcp_request_opens_client_tab`
- [x] **STEP 4: Development**
  - [x] Added `mcp_client_migration.request_data_to_mcp_client`
  - [x] Removed MCP from HTTP method combo and `_execute_mcp` dispatch
  - [x] Routed legacy `method:MCP` opens through `open_legacy_mcp_request_tab`
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Technical Debt Analysis**
- [x] **STEP 8: Dev Docs**
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1171/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1171/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_mcp_client_migration.py`

### STEP 4: Development

- `pypost/core/mcp_client_migration.py`
- `pypost/ui/presenters/tabs_presenter.py`
- `pypost/core/request_service.py`
- `pypost/ui/widgets/request_editor.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1171/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1171/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1171/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_integration.md`, `doc/dev/request_execution.md`, `doc/dev/mcp_client_draft_tab.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above.
