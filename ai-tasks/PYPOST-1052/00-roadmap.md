# Roadmap: PYPOST-1052

## Task Metadata

- **Implementation language**: Python
- **Branch name**: feature/PYPOST-1052-widen-mcp-request-discovery

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1052/00-roadmap.md` — task progress journal and implementation language recorded.
  - `ai-tasks/PYPOST-1052/10-requirements.md` — business and functional requirements for widening agent input discovery in MCP tool definitions.
- [x] **STEP 2: High-Level Architecture Design**
  - Research baseline requirements and existing parameter discovery in `pypost/core/mcp_secrets_policy.py`.
  - Inventory consumers (`pypost/core/mcp_tool_contract.py`, `pypost/core/mcp_server_impl.py`, `pypost/ui/widgets/request_editor.py`, `tests/test_example_fixtures.py`).
  - Formulate failing repro test design for Step 3 covering function-wrapped `mcp.request` expressions.
  - Detail architectural components, interfaces, sequence diagram, and Definition of Done traceability in `ai-tasks/PYPOST-1052/20-architecture.md`.
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_mcp_secrets_policy.py`
  - [x] `tests/test_mcp_tool_contract.py`
  - [x] `tests/test_request_editor_mcp_params.py`
- [x] **STEP 4: Development**
  - [x] Updated `_MCP_REQUEST_VAR_PATTERN` in `pypost/core/mcp_secrets_policy.py` to `re.compile(r"mcp\.request\.([a-zA-Z0-9_]+)")` and updated docstrings.
  - [x] Verified all unit and contract tests in `tests/test_mcp_secrets_policy.py`, `tests/test_mcp_tool_contract.py`, `tests/test_request_editor_mcp_params.py`, and `tests/test_example_fixtures.py` turn GREEN (57/57 passing).
- [x] **STEP 5: Code Cleanup**
  - [x] Ran `make lint` and `flake8` static analysis across touched files (`pypost/core/mcp_secrets_policy.py`, `tests/test_mcp_secrets_policy.py`, `tests/test_mcp_tool_contract.py`, `tests/test_request_editor_mcp_params.py`) — 0 errors/warnings.
  - [x] Fixed import ordering, line lengths (≤100 chars), decorator spacing, and trailing whitespace.
  - [x] Verified full test suite for touched modules and MCP components (112/112 passing) with explicit timeout markers.
  - [x] Created `ai-tasks/PYPOST-1052/40-code-cleanup.md`.
- [x] **STEP 6: Observability**
  - [x] Analyzed logging and metrics requirements for MCP request parameter discovery widening.
  - [x] Confirmed `McpSecretsPolicy.safe_execution_log_fields` provides safe diagnostic count logging without exposing secret names or parameter values.
  - [x] Verified MCP tool discovery and schema generation remain deterministic with existing `MCPServerImpl` DEBUG/INFO logging and Prometheus metrics.
  - [x] Created `ai-tasks/PYPOST-1052/50-observability.md`.
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyzed shortcuts taken, code quality, missing tests, and performance implications.
  - [x] Verified explicit timeout markers across all touched test suites (`test_mcp_secrets_policy.py`, `test_mcp_tool_contract.py`, `test_request_editor_mcp_params.py`, `test_example_fixtures.py`).
  - [x] Verified closure of PYPOST-1028 TD-2 (widened `McpSecretsPolicy` discovery).
  - [x] Documented non-blocking pre-existing tech debt (PYPOST-1049, PYPOST-1033/1034).
  - [x] Completed Blocker Review concluding SAFE TO CLOSE.
  - [x] Created `ai-tasks/PYPOST-1052/60-tech-debt.md`.
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/mcp_secrets_policy.md` policy rules table and `McpSecretsPolicy.extract_mcp_request_variables` API documentation to reflect bare and function-wrapped `mcp.request.VAR` expressions discovery.
  - [x] Updated `doc/dev/mcp_integration.md` Schema Generation and pipeline diagram to document bare and function-wrapped placeholder discovery.
  - [x] Updated `doc/dev/testing.md` to reflect production `McpSecretsPolicy.extract_mcp_request_variables` alignment with the broad fixture test scanner.
  - [x] Checked all Definition of Done criteria in `ai-tasks/PYPOST-1052/10-requirements.md`.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1052/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1052/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1052/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1052/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1052/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_secrets_policy.md` — updated `McpSecretsPolicy.extract_mcp_request_variables` API doc and policy rules table for bare & wrapped expressions.
- `doc/dev/mcp_integration.md` — updated Schema Generation overview and pipeline diagram for function-wrapped agent parameter discovery.
- `doc/dev/testing.md` — updated contract test documentation reflecting alignment of production discovery with the fixture test scanner.
- `ai-tasks/PYPOST-1052/10-requirements.md` — marked all Definition of Done criteria complete.

### COMMIT

- [x] Committed on branch `dev` — hash `98eaf969`
- Message: `feature(mcp): PYPOST-1052 widen McpSecretsPolicy discovery for wrapped request forms`
