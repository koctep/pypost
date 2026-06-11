# Roadmap: PYPOST-555

## Programming Language

Python 3.11+ (PyPost / PySide6)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] `mcp_tool_contract.py` — shared preview builder matching `list_tools`
  - [x] MCP tab agent preview panel in `RequestWidget`
  - [x] Unit tests for contract preview and policy exclusions
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

- `ai-tasks/PYPOST-555/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-555/20-architecture.md`

### STEP 3: Development

- `pypost/core/mcp_tool_contract.py`
- `pypost/ui/widgets/request_editor.py`
- `pypost/ui/presenters/tabs_presenter.py`
- `tests/test_mcp_tool_contract.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-555/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-555/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-555/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-555/70-dev-docs.md`
- `doc/dev/mcp_integration.md`
