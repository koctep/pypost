# Roadmap: PYPOST-1412

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Document business goals, user stories, acceptance criteria, and domain entities for integration test suite, compatibility matrix, and developer documentation
  - [x] Create requirements artifact in `ai-tasks/PYPOST-1412/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Design integration harness, compatibility matrix, and documentation plan in `ai-tasks/PYPOST-1412/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_collection_scoped_variables_integration.py`
- [x] **STEP 4: Development**
  - [x] Implemented template substitution in `CollectionVariablesIntegrationHarness.run_unified_lifecycle` using `TemplateService.render_string` (preserving `template_service.py` <= 265 line baseline cap)
  - [x] Implemented `CollectionVariablesIntegrationHarness.run_unified_lifecycle` in `tests/test_collection_scoped_variables_integration.py` covering catalog discovery, standalone MCP server startup, workspace environment import, and template rendering
  - [x] Verified complete end-to-end integration lifecycle test passes along with 4-quadrant compatibility matrix and diagnostic safety
  - [x] Verified no regressions in child story test suites (`test_collection_scoped_variables_repro.py`, `test_mcp_standalone_execution_repro.py`, `test_workspace_environment_import_repro.py`)
  - [x] Quality gates verified: `make lint`, `make typecheck`, `make verify-ai-tasks`
- [x] **STEP 5: Code Cleanup**
  - [x] Review implementation against SOLID principles, dead code, unused imports, and formatting
  - [x] Create artifact `ai-tasks/PYPOST-1412/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Analyze logging, caplog assertion contracts, and secret masking boundaries
  - [x] Create artifact `ai-tasks/PYPOST-1412/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze technical debt, shortcuts, compromises, and follow-ups in `ai-tasks/PYPOST-1412/60-tech-debt.md`
  - [x] Blocker review completed (SAFE TO CLOSE)
  - [x] Follow-up Jira issues estimated and created (PYPOST-1416, PYPOST-1417, PYPOST-1418)
- [x] **STEP 8: Dev Docs**
  - [x] Update developer documentation in `doc/dev/collection_scoped_variables.md`
  - [x] Update documentation index in `doc/dev/README.md`
  - [x] Create artifact `ai-tasks/PYPOST-1412/70-dev-docs.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1412/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1412/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_collection_scoped_variables_integration.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1412/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1412/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1412/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`
- `ai-tasks/PYPOST-1412/70-dev-docs.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
