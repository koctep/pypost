# Roadmap: PYPOST-952

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_ui_actions_mcp.py`
- [x] **STEP 4: Development**
  - [x] `pypost/agent/ui_actions_mcp.py` — stdio MCP bridge wrapping ui_actions
  - [x] `pyproject.toml` console script `pypost-agent-ui-mcp`
  - [x] Makefile `run-agent-ui-mcp` packaging entry
  - [x] Green unit + stdio integration tests
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-952/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-952/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_ui_actions_mcp.py`

### STEP 4: Development

- `pypost/agent/ui_actions_mcp.py`
- `pyproject.toml` — `[project.scripts]`
- `Makefile` — `run-agent-ui-mcp`
- `tests/test_agent_ui_actions_mcp.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-952/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-952/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-952/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/agent_ui_actions_mcp.md`
- `doc/dev/ui_actions.md` (packaging section update)
