# Roadmap: PYPOST-1028

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] Red tests in `tests/test_example_fixtures.py` (PYPOST-1028 section):
        positive + mutation negatives for companion env coverage, Basic auth
        convention, `mcp.request.*` ↔ `mcp_params`, fixed-input allowlist
        freeze, and agent-driven query/body — call checkers not yet
        implemented (`assert_jira_mcp_*` / `FIXED_INPUT_JIRA_MCP_REQUEST_IDS`)
- [x] **STEP 4: Development**
  - [x] Iteration 1: Implemented `FIXED_INPUT_JIRA_MCP_REQUEST_IDS` and
        `assert_jira_mcp_*` checkers (env coverage, auth, mcp_params, allowlist
        freeze, agent-driven) in `tests/test_example_fixtures.py`; no fixture
        JSON changes; Step 3 suite green via `make test
        PYTEST_ARGS='tests/test_example_fixtures.py -v'`
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

- **Primary:** Python for the existing offline fixture-contract suite.
- **Fixture input:** JSON Jira MCP collection and its companion environment;
  this task protects their existing agreement and does not deliver new Jira
  capabilities.
- **Documentation:** English Markdown for the top-down task artifacts.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1028/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1028/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/`

### STEP 4: Development

- Focused offline fixture-contract changes only

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1028/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1028/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1028/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

## Recommended branch name

`test/PYPOST-1028-strengthen-jira-fixture-contracts`
