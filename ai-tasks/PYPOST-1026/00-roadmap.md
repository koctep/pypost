# Roadmap: PYPOST-1026

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `test_example_fixtures.py::test_jira_mcp_collection_imports_via_native_loader`
        — `len(requests) >= 18` + all `expose_as_mcp` + placeholder hygiene;
        red on current 12-request starter
  - [x] `test_example_fixtures.py::test_jira_mcp_collection_covers_required_skill_capabilities`
        — locked ids/path markers: create sprint, sprint membership,
        get sprint issues, epic/parent link, comment, assign
  - [x] `test_example_fixtures.py::test_jira_cloud_environment_imports_with_placeholders`
        — keep green: placeholders, `hidden_keys`, `enable_mcp`
- [x] **STEP 4: Development**
  - [x] Added sprint MCP requests: create, add issues, get sprint issues
  - [x] Added issue MCP requests: parent link, comment, assign (18 total)
  - [x] Added stretch requests: get worklog, move to backlog, assignable users
        (21 MCP-exposed requests)
  - [x] Updated `examples/README.md` inventory + Coverage vs gaps section
  - [x] Contract tests green for expanded jira-mcp surface
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

- **Primary**: JSON for importable example fixtures under `examples/`, plus
  English Markdown for import/use and coverage documentation
  (`.cursor/lsr/do-markdown.md`)
- **Tests / tiny fixes**: Python in the existing examples/fixtures/tests
  ecosystem (`.cursor/lsr/do-python.md`) when contract checks must change
- **Application code**: none in scope unless a tiny fixture/docs/test fix is
  required; no new product features

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1026/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1026/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1026/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1026/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1026/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

## Suggested branch

`feature/PYPOST-1026-expand-jira-mcp-collection`
