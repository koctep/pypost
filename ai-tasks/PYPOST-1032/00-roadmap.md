# Roadmap: PYPOST-1032

## STEP 1 Approval Record

The applicable `sprint-runner` workflow explicitly runs its phases in
autonomous mode and preauthorizes proceeding without a separate confirmation
between phases. That explicit autonomous preapproval is the required approval
basis before marking STEP 1 complete.

## STEP 2 Approval Record

The same `sprint-runner` autonomous-mode authorization is the approval basis
for this architecture review. The design is recorded in
`20-architecture.md`; no separate pause is required before Step 3.

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_example_fixtures.py::test_jira_project_default_is_wired_as_soft_guidance`
    — independently reviewed deterministic offline red contract for the Jira
    project soft-default behavior.
- [x] **STEP 4: Development**
  - [x] Added the visible Jira project-key placeholder, supported board filter,
    soft-default MCP guidance, and importer safety guidance.
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

- **Primary**: English Markdown for the user-facing guidance.
- **Structured example data**: JSON, if later design confirms it is needed.
- **Application code**: none in scope.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1032/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1032/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1032/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1032/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1032/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/jira_mcp_project_default.md`
- `doc/dev/README.md` (MCP index entry)
- `ai-tasks/PYPOST-1032/70-dev-docs.md`

## Suggested branch

`feature/PYPOST-1032-soft-project-scope-jira-mcp-examples`
