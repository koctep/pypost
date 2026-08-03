# Roadmap: PYPOST-1027

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *Contract regression test for the protected stretch Jira MCP tools in `tests/test_example_fixtures.py` (reviewed red: current contract omits `jira-get-worklog` and `jira-search-assignable-users`)*
- [x] **STEP 4: Development**
  - [x] *Added one immutable protected-operation table that extends required IDs and parametrically locks each Jira method/route contract offline.*
- [x] **STEP 5: Code Cleanup**
  - [x] *Focused fixture-contract tests and flake8 pass; no production or fixture cleanup was warranted.*
- [x] **STEP 6: Observability**
  - [x] *Runtime observability is N/A for the offline fixture-contract test; focused pytest is the deterministic CI signal.*
- [x] **STEP 7: Review and Technical Debt**
  - [x] *Independent review passed; no in-scope technical debt or user-facing documentation change was identified.*
- [x] **STEP 8: Dev Docs**
  - [x] *Updated the developer fixture-contract guide and index; independent
    documentation review passed, with no user-facing docs needed for this
    test-only change.*

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

- **Primary:** Python for the existing offline fixture-contract suite.
- **Fixture input:** JSON is read from the existing curated Jira MCP example
  collection; this task does not add, remove, or redesign collection requests.
- **Documentation:** English Markdown only for the top-down task artifacts;
  no user-facing documentation change is required unless a later step finds a
  genuine documentation gap.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1027/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1027/20-architecture.md`

### STEP 3: Failing Repro

- Automated contract regression test under `tests/`

### STEP 4: Development

- Focused test/fixture-contract update only

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1027/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1027/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1027/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md` records the protected stretch-operation fixture
  contract and its focused offline check; no user-facing behavior changes.

## Recommended branch name

`test/PYPOST-1027-lock-jira-mcp-stretch-contracts`
