# Roadmap: PYPOST-136

**Language:** Python (PySide6)

**Suggested branch:** `fix/PYPOST-136-mcp-tools-restart-on-update`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Wire `EnvPresenter.refresh_mcp_tools()` on collection/request changes
  - [x] Harden `MCPServerManager.update_tools()` with signature check and logging
  - [x] Unit tests for manager and presenter
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

- `ai-tasks/PYPOST-136/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-136/20-architecture.md`

### STEP 3: Development

- `pypost/core/mcp_server.py`
- `pypost/ui/presenters/env_presenter.py`
- `pypost/ui/main_window.py`
- `tests/test_mcp_server_manager.py`
- `tests/test_env_presenter.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-136/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-136/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-136/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/mcp_integration.md`
- `ai-tasks/PYPOST-136/70-dev-docs.md`
