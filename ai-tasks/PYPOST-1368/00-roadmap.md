# Roadmap: PYPOST-1368

## Task Metadata

- **Implementation language**: Markdown (planning artifacts) + Jira process; child implementation stories under PYPOST-1284 use Python.

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Analyze parent epic PYPOST-1284 and existing MCP library variable configuration
  - [x] Create decomposition notes in `ai-tasks/PYPOST-1284/decomposition-notes.md`
  - [x] Create requirements artifact in `ai-tasks/PYPOST-1368/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Draft system architecture and decomposition workflow in `ai-tasks/PYPOST-1368/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] N/A — no behavioral change (decomposition and planning task; red tests belong in child stories WIZARD-1 to WIZARD-4)
- [x] **STEP 4: Development**
  - [x] Create child Jira tasks linked to PYPOST-1284 and assign to sprint 2029:
    - [x] `PYPOST-1372` (3 SP, provisional `WIZARD-1`): `[PYPOST-1284] Extend CollectionVariable schema with help_text guidance attribute` (Parent: PYPOST-1284, Sprint: 2029)
    - [x] `PYPOST-1373` (5 SP, provisional `WIZARD-2`): `[PYPOST-1284] Implement VariableSetupWizardDialog and expandable VariableGuidanceCard component` (Parent: PYPOST-1284, Sprint: 2029)
    - [x] `PYPOST-1374` (5 SP, provisional `WIZARD-3`): `[PYPOST-1284] Integrate variable setup wizard launch and overlay persistence in MCP server editor` (Parent: PYPOST-1284, Sprint: 2029)
    - [x] `PYPOST-1375` (3 SP, provisional `WIZARD-4`): `[PYPOST-1284] Add reference collection with OAuth setup guidance and contract test suite` (Parent: PYPOST-1284, Sprint: 2029)
- [x] **STEP 5: Code Cleanup**
  - [x] Perform static code analysis and link validation via `make lint` and `make verify-ai-tasks`
  - [x] Artifact formatting and consistency check across planning documents
  - [x] Draft cleanup report in `ai-tasks/PYPOST-1368/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Process observability: document Top-Down per-step worklog auditing and token consumption tracking
  - [x] Jira traceability: audit ticket linkage to parent epic PYPOST-1284 and Sprint 2029
  - [x] Specify downstream observability requirements for child stories (PYPOST-1372, PYPOST-1373, PYPOST-1374, PYPOST-1375)
  - [x] Define logging levels, structured events, and secret masking rules for wizard execution
  - [x] Draft observability artifact in `ai-tasks/PYPOST-1368/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze shortcuts taken during decomposition (create-time self-estimation, deferred Jira issue linking)
  - [x] Audit code quality and test coverage requirements (confirm N/A for decomposition ticket, verify zero timeout-marker blockers)
  - [x] Identify non-blocking technical debt and process residuals (sequencing, secret masking, cross-platform testing)
  - [x] Document follow-up child stories (PYPOST-1372, PYPOST-1373, PYPOST-1374, PYPOST-1375) with priorities, story points, and scopes
  - [x] Draft technical debt artifact in `ai-tasks/PYPOST-1368/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Record developer documentation strategy and minimal pointer decision for decomposition task
  - [x] Add concise developer documentation pointer in `doc/dev/mcp_server_registry.md` referencing epic PYPOST-1284 and child stories PYPOST-1372..1375
  - [x] Create `ai-tasks/PYPOST-1368/70-dev-docs.md` artifact
  - [x] Gate: leave Step 8 `[/]` until review / acceptance
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1368/10-requirements.md`
- `ai-tasks/PYPOST-1284/decomposition-notes.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1368/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code / Jira tickets
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1368/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1368/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1368/60-tech-debt.md`

### STEP 8: Dev Docs

- `ai-tasks/PYPOST-1368/70-dev-docs.md`
- `doc/dev/mcp_server_registry.md` pointer note

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
