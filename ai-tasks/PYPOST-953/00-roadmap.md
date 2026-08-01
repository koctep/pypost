# Roadmap: PYPOST-953

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *`tests/test_mcp_server_impl.py::TestMCPServerImpl::test_list_tools_excludes_agent_ui_action_names` (guard — green on first run; invariant already holds)*
- [x] **STEP 4: Development**
  - [x] Added runtime catalog exclusion test to canonical `test_mcp_server_impl.py`
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (`.cursor/lsr/do-python.md`); developer docs in English Markdown.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-953/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-953/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_mcp_server_impl.py` — runtime guard on `MCPServerImpl.list_tools()`

### STEP 4: Development

- `tests/test_mcp_server_impl.py` — catalog exclusion assert (no production change)

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-953/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-953/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-953/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/agent_ui_actions_mcp.md`, `doc/dev/testing.md`
