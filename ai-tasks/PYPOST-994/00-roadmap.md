# Roadmap: PYPOST-994

## Task Metadata

- **Implementation language**: Python
- **Branch name**: feature/PYPOST-994-deduplicate-mcp-catalog-exclusion-asserts

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Gather requirements for deduplicating MCP catalog exclusion asserts
  - [x] Produce requirements artifact `ai-tasks/PYPOST-994/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Establish `tests/test_mcp_server_impl.py` as authoritative lock for MCP catalog tool exclusion
  - [x] Keep `tests/test_agent_ui_actions_mcp.py` dedicated to sidecar process, entrypoint, and import separation
  - [x] Produce architecture artifact `ai-tasks/PYPOST-994/20-architecture.md`
- [x] **STEP 3: Failing Repro / Test Baseline**
  - [x] Identify redundant assertions in `tests/test_agent_ui_actions_mcp.py` duplicating `tests/test_mcp_server_impl.py`
- [x] **STEP 4: Development**
  - [x] Remove duplicate `test_mcpserver_impl_catalog_excludes_agent_ui_tools` and unused `MCPServerImpl` import from `tests/test_agent_ui_actions_mcp.py`
  - [x] Verify authoritative `test_list_tools_excludes_agent_ui_action_names` in `tests/test_mcp_server_impl.py`
- [x] **STEP 5: Code Cleanup**
  - [x] Run `make lint` and `make verify-ai-tasks`
  - [x] Produce `ai-tasks/PYPOST-994/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Verify test coverage signals and execution integrity
  - [x] Produce `ai-tasks/PYPOST-994/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Review technical debt status
  - [x] Produce `ai-tasks/PYPOST-994/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Document test architecture separation in dev docs if applicable
- [ ] **COMMIT: Commit Changes**
  - Commit hash and message (Conventional Commits + JIRA ID)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

## Artifacts

### STEP 1: Requirements
- `ai-tasks/PYPOST-994/10-requirements.md`

### STEP 2: Architecture
- `ai-tasks/PYPOST-994/20-architecture.md`

### STEP 4: Development
- Source code / Test files

### STEP 5: Code Cleanup
- `ai-tasks/PYPOST-994/40-code-cleanup.md`

### STEP 6: Observability
- `ai-tasks/PYPOST-994/50-observability.md`

### STEP 7: Technical Debt
- `ai-tasks/PYPOST-994/60-tech-debt.md`

### COMMIT
- Commit hash and message (Conventional Commits + JIRA ID)
