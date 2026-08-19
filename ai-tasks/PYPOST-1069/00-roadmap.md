# Roadmap: PYPOST-1069

## Task Metadata

- **Implementation language**: Python
- **Branch name**: feature/PYPOST-1069-multi-project-jira-mcp-key

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Document business requirements and functional scope for comma-separated `jira_project_key` in Jira MCP
  - [x] Define acceptance criteria (DoD) for multiple project keys, whitespace normalization, search JQL `in (...)`, and board discovery
  - [x] Produce requirements artifact `ai-tasks/PYPOST-1069/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Design architecture for multi-project key normalization, JQL search guidance `project in (...)`, and board listing
  - [x] Document target architecture, Mermaid sequence flows, entity contracts, and DoD matrix
  - [x] Create architecture artifact `ai-tasks/PYPOST-1069/20-architecture.md`
- [x] **STEP 3: Failing Repro Test / Verification Test**
  - [x] Add failing tests verifying multi-project key guidance and normalization in `tests/test_example_fixtures.py` and integration tests
  - [x] Confirm RED failure before production edits
- [x] **STEP 4: Development**
  - [x] Update `examples/collections/jira_mcp.json` descriptions and guidance for multi-project key lists
  - [x] Verify single key backward compatibility and multi-key support across tests
  - [x] Ensure all tests pass GREEN
- [x] **STEP 5: Code Cleanup**
  - [x] Run `make lint` and `make check-mcp-fixtures`
  - [x] Produce `ai-tasks/PYPOST-1069/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Document observability impact, metrics, and logging behavior
  - [x] Produce `ai-tasks/PYPOST-1069/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze technical debt and follow-up opportunities
  - [x] Produce `ai-tasks/PYPOST-1069/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Update developer documentation in `doc/dev/jira_mcp_project_default.md` and `examples/README.md`
  - [x] Produce `ai-tasks/PYPOST-1069/70-dev-docs.md`
- [x] **COMMIT: Commit Changes**
  - Commit: `6ad830c6` feat(mcp): support comma-separated projects in jira_project_key (PYPOST-1069)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

## Artifacts

### STEP 1: Requirements
- `ai-tasks/PYPOST-1069/10-requirements.md`

### STEP 2: Architecture
- `ai-tasks/PYPOST-1069/20-architecture.md`

### STEP 3: Failing Repro / Verification Test
- `tests/test_example_fixtures.py`

### STEP 4: Development
- `examples/collections/jira_mcp.json`
- `tests/test_example_fixtures.py`

### STEP 5: Code Cleanup
- `ai-tasks/PYPOST-1069/40-code-cleanup.md`

### STEP 6: Observability
- `ai-tasks/PYPOST-1069/50-observability.md`

### STEP 7: Technical Debt
- `ai-tasks/PYPOST-1069/60-tech-debt.md`

### STEP 8: Dev Docs
- `doc/dev/jira_mcp_project_default.md`
- `examples/README.md`
- `ai-tasks/PYPOST-1069/70-dev-docs.md`

### COMMIT
- `6ad830c6` feat(mcp): support comma-separated projects in jira_project_key (PYPOST-1069)
