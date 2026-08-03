# Roadmap: PYPOST-1029

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *Pagination `mcp_params` contract on board/sprint list requests*
  - Red tests: `tests/test_example_fixtures.py`
    (`test_jira_mcp_list_requests_expose_pagination_mcp_params`,
    `test_jira_mcp_list_boards_leaves_fixed_input_allowlist`)
- [x] **STEP 4: Development**
  - [x] Parameterized `maxResults`/`startAt` on three list requests in
    `examples/collections/jira_mcp.json`
  - [x] Narrowed `FIXED_INPUT_JIRA_MCP_REQUEST_IDS` to current-user only
  - [x] Scoped PYPOST-1038 path-ID freeze to URL `to_int`; updated
    integration path extras for pagination args
  - [x] Green: `make test PYTEST_ARGS='tests/test_example_fixtures.py -v'`
- [x] **STEP 5: Code Cleanup**
  - [x] `40-code-cleanup.md`; lint + timeout validation
- [x] **STEP 6: Observability**
  - [x] `50-observability.md` — N/A (fixture/contract only)
- [x] **STEP 7: Review and Technical Debt**
  - [x] `60-tech-debt.md` — TD-1 optional defaults; TD-2 token pagination;
    SAFE TO CLOSE
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/testing.md`, `doc/dev/jira_mcp_project_default.md`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (fixture-contract tests); curated Jira MCP collection JSON

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1029/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1029/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_example_fixtures.py` (PYPOST-1029 pagination contracts)

### STEP 4: Development

- `examples/collections/jira_mcp.json`
- `tests/test_example_fixtures.py`
- `tests/test_mcp_server_integration.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1029/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1029/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1029/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md`
- `doc/dev/jira_mcp_project_default.md`
