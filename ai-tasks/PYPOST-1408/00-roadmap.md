# Roadmap: PYPOST-1408

## Task Metadata

- **Implementation language**: Markdown (planning artifacts) + Jira process; child implementation stories under PYPOST-1407 use Python.

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Analyze parent epic PYPOST-1407 and existing codebase (collection models, library manifests, MCP servers dialog, environment variables widget)
  - [x] Create decomposition notes in `ai-tasks/PYPOST-1407/decomposition-notes.md`
  - [x] Create requirements artifact in `ai-tasks/PYPOST-1408/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Draft system architecture and decomposition workflow in `ai-tasks/PYPOST-1408/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] N/A — no behavioral change (decomposition and planning task; red tests belong in child stories COLVAR-1 to COLVAR-4)
- [x] **STEP 4: Development**
  - [x] Create child Jira tasks linked to PYPOST-1407 and assign to sprint 2033:
    - [x] `PYPOST-1409` (3 SP, provisional `COLVAR-1`): `[PYPOST-1407] Eliminate library-level variables and establish collection-scoped variables and catalog manifest` (Parent: PYPOST-1407, Sprint: 2033)
    - [x] `PYPOST-1410` (5 SP, provisional `COLVAR-2`): `[PYPOST-1407] Standalone MCP server configuration and execution without workspace environment` (Parent: PYPOST-1407, Sprint: 2033)
    - [x] `PYPOST-1411` (3 SP, provisional `COLVAR-3`): `[PYPOST-1407] Workspace environment variable import action from collections` (Parent: PYPOST-1407, Sprint: 2033)
    - [x] `PYPOST-1412` (3 SP, provisional `COLVAR-4`): `[PYPOST-1407] Integration test suite, compatibility matrix, and developer documentation` (Parent: PYPOST-1407, Sprint: 2033)
- [x] **STEP 5: Code Cleanup**
  - [x] Perform static code analysis and linting via `make lint` and `make verify-ai-tasks`
  - [x] Verify markdown structure, relative links, and formatting
  - [x] Document code cleanup report in `ai-tasks/PYPOST-1408/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Document verdict: DECOMPOSE / Jira-only (no product runtime observability changes on this ticket)
  - [x] Establish process observability: per-step worklog auditing, token consumption tracking, and bidirectional Jira traceability
  - [x] Formulate downstream observability specifications for child stories PYPOST-1409 through PYPOST-1412
  - [x] Complete observability report in `ai-tasks/PYPOST-1408/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Document technical debt and future maintenance considerations in `ai-tasks/PYPOST-1408/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Document task summary and child story tracking
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1408/10-requirements.md`
- `ai-tasks/PYPOST-1407/decomposition-notes.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1408/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1408/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1408/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1408/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/collection_scoped_variables.md`
- `ai-tasks/PYPOST-1408/70-dev-docs.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
