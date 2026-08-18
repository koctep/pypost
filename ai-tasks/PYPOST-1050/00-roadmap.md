# Roadmap: PYPOST-1050

## Task Metadata

- **Implementation language**: Python
- **Branch name**: documentation/PYPOST-1050-document-backlog-batch-limit

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Gather business goals, user stories, and acceptance criteria
  - [x] Document scope, boundaries, non-functional requirements, entities, and Q&A
  - [x] Create `ai-tasks/PYPOST-1050/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Research Atlassian Agile REST API backlog batch limit and existing test/fixture contracts
  - [x] Design failing repro for Step 3 via `tests/test_example_fixtures.py` locked discoverability substrings
  - [x] Define architecture, Mermaid diagram, interfaces, and DoD traceability in `20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_example_fixtures.py::test_jira_mcp_shipped_descriptions_carry_discoverability_guidance[jira-move-issues-to-backlog-required_substrings1]`
- [x] **STEP 4: Development**
  - [x] Document Agile ≤50 backlog batch limit in `examples/collections/jira_mcp.json` (`jira-move-issues-to-backlog`) and `examples/README.md`; verify all contract and mutation tests pass green
- [x] **STEP 5: Code Cleanup**
  - [x] Run static analysis (`make lint`, `flake8 tests/test_example_fixtures.py`) and fix formatting/line lengths
  - [x] Run test suite (`QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_example_fixtures.py`)
  - [x] Create `ai-tasks/PYPOST-1050/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Document observability analysis (production logging/metrics N/A; test assertion diagnostic observability in assert_jira_mcp_discoverability_guidance)
  - [x] Create `ai-tasks/PYPOST-1050/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze shortcuts taken, code quality, missing tests, and performance
  - [x] Review explicit pytest timeout markers (module-level `pytestmark = pytest.mark.timeout(30)`)
  - [x] Document follow-up tasks and provide Blocker Review concluding SAFE TO CLOSE
  - [x] Create `ai-tasks/PYPOST-1050/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Update `doc/dev/testing.md` Jira MCP discoverability contracts section with PYPOST-1050 reference, `'50'` in locked lowercase fragments table, and sorted `['50', 'membership', 'remove-from-sprint']` mutation contract
  - [x] Update Definition of Done in `ai-tasks/PYPOST-1050/10-requirements.md`
- [ ] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1050/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1050/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1050/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1050/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1050/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md` (Jira MCP discoverability contracts section updated with PYPOST-1050 reference, locked fragment `'50'`, and mutation diagnostic message contract)

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID)
