# Roadmap: PYPOST-1047

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *Extend `tests/test_example_fixtures.py`: floor ≥22; lock
    `jira-delete-sprint` (DELETE) + `jira-move-issues-to-backlog` (POST)*
  - Test path: `tests/test_example_fixtures.py`
    (`JIRA_MCP_MIN_EXPOSED_REQUESTS=22`, required ids + method/path markers)
- [x] **STEP 4: Development**
  - [x] Added `jira-delete-sprint` (DELETE Agile sprint, expose_as_mcp)
  - [x] Sharpened `jira-move-issues-to-backlog` mcp_description (remove path)
  - [x] Updated `examples/README.md` and `doc/dev/testing.md` counts/lists
  - [x] Step 3 contract tests green (`tests/test_example_fixtures.py` 4 passed)
- [x] **STEP 5: Code Cleanup**
  - [x] `make lint` clean; fixture contract tests green (4 passed)
  - [x] Synced `doc/dev/README.md` TOC anchor for PYPOST-1047 heading
  - [x] Line-length / coverage-table cleanup in `examples/README.md`
  - Artifact: `ai-tasks/PYPOST-1047/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] N/A — fixtures/docs/tests only; relies on existing MCP/HTTP logging
    and Prometheus instruments (no new `pypost/` runtime paths)
  - Artifact: `ai-tasks/PYPOST-1047/50-observability.md`
- [x] **STEP 7: Review and Technical Debt**
  - [x] Artifact: `ai-tasks/PYPOST-1047/60-tech-debt.md` (SAFE TO CLOSE;
    Low TD-1/TD-2; out-of-scope TD-3 verify-ai-tasks baseline drift)
- [x] **STEP 8: Dev Docs**
  - [x] Agent-facing API + troubleshooting in `doc/dev/testing.md`
  - [x] DoD checkboxes closed in `10-requirements.md`
  - [x] Artifact: `ai-tasks/PYPOST-1047/70-dev-docs.md`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

- **Primary**: JSON for the curated jira-mcp example collection under
  `examples/`, plus English Markdown for companion docs
  (`.cursor/lsr/do-markdown.md`)
- **Tests / contract updates**: Python in the existing fixtures/tests
  ecosystem (`.cursor/lsr/do-python.md`) when counts, expose-as-MCP checks,
  or smoke/regression coverage must change
- **Application code / Atlassian MCP**: out of scope — collection, docs, and
  tests only; no product feature work and no changes to the external
  Atlassian MCP server

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1047/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1047/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1047/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1047/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1047/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/` (primarily `testing.md`; TOC in `README.md`)
- `ai-tasks/PYPOST-1047/70-dev-docs.md`

## Recommended branch name

`feature/PYPOST-1047-jira-mcp-delete-sprint`
