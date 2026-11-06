# Roadmap: PYPOST-1342

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1342/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1342/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_mcp_tool_contract.py::test_schema_emits_enum_and_array_items`
  - `tests/test_mcp_tool_contract.py::test_validate_rejects_value_outside_enum`
  - `tests/test_mcp_tool_contract.py::test_validate_rejects_array_item_type_mismatch`
- [x] **STEP 4: Development**
  - [x] Extended `McpToolParam` with optional `enum` / `items` + construct checks
  - [x] Schema emission + `validate_mcp_argument_values` enforcement
  - [x] `McpParamsTable` Enum/Items columns (7-column UI)
  - [x] Tightened GitHub/GitLab curated MCP JSON params
  - [x] Updated collection contract Arg/`_expected_schema` helpers and UI tests
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1342/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1342/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1342/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - `doc/dev/mcp_integration.md` (Enum and array items section)
  - `doc/dev/github_mcp_collection.md` (review event enum note + follow-up status)
  - `doc/dev/gitlab_mcp_collection.md` (closed enum note)
- [ ] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[x]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1342/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1342/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_mcp_tool_contract.py` (PYPOST-1342 enum/items repros)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1342/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1342/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1342/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_integration.md`
- `doc/dev/github_mcp_collection.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
