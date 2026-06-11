# Roadmap: PYPOST-556

**Language:** Python 3.11+ (PyPost standard)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Reliable MCP server startup signaling (listen before ON)
  - [x] Port-busy / bind failure surfaced to UI
  - [x] MCP tools overview dialog in top bar
  - [x] Unit and integration tests
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-556/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-556/20-architecture.md`

### STEP 3: Development

- `pypost/core/mcp_server.py`
- `pypost/core/mcp_server_impl.py`
- `pypost/ui/dialogs/mcp_tools_overview_dialog.py`
- `pypost/ui/presenters/env_presenter.py`
- `tests/test_mcp_server_manager.py`
- `tests/test_env_presenter.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-556/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-556/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-556/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/mcp_integration.md`
