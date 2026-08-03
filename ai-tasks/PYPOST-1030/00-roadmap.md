# Roadmap: PYPOST-1030

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *Critical REST path catalog contract*
  - Red test: `tests/test_example_fixtures.py`
    (`test_jira_mcp_critical_rest_paths_match_locked_catalog`) — failed on
    missing `examples/collections/jira_mcp_critical_rest_paths.json`
- [x] **STEP 4: Development**
  - [x] Added `examples/collections/jira_mcp_critical_rest_paths.json`
  - [x] Catalog compare helpers + green critical-path test
  - [x] `make check-jira-mcp-path-freshness` Makefile target
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/jira_mcp_path_freshness.md`, `testing.md`, `README.md`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (offline fixture-contract tests); curated JSON catalog + Markdown docs

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1030/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1030/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_example_fixtures.py`
  (`test_jira_mcp_critical_rest_paths_match_locked_catalog`)

### STEP 4: Development

- `examples/collections/jira_mcp_critical_rest_paths.json`
- `tests/test_example_fixtures.py`
- `Makefile` (`check-jira-mcp-path-freshness`)

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1030/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1030/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1030/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/jira_mcp_path_freshness.md`
- `doc/dev/testing.md`
- `doc/dev/README.md`
