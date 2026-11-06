# Roadmap: PYPOST-1343

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1343/10-requirements.md`
  - Implementation language: Python
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1343/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_json_string_to_json.py`
    (`test_function_registry_includes_to_json`,
    `test_to_json_preserves_list_dict_bool_number`;
    `test_to_json_string_still_stringifies_list` is a green compatibility lock)
- [x] **STEP 4: Development**
  - [x] Iteration 1: Added `to_json` in `json_string.py`, registered in
    `function_registry.py`; Step 3 tests green
  - [x] Iteration 2: Simplified GitHub MCP bodies (labels/assignees/inputs/draft/
    enable_debug_logging) and inputs MCP description
  - [x] Iteration 3: Updated locked GitHub/registry/1077 tests for type-preserving
    dispatch inputs; GitLab suite still green (string bodies unchanged)
  - [x] Iteration 4: Updated `doc/dev/github_mcp_collection.md`,
    `template_expression_functions.md`, `examples/README.md`
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1343/40-code-cleanup.md`
  - Note: full `make lint` blocked by pre-existing E501 in
    `tests/test_mcp_server_registry.py:308` (PYPOST-1362)
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1343/50-observability.md` (N/A — pure helper; no new logs/metrics)
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1343/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/template_expression_functions.md`
  - Updated `doc/dev/github_mcp_collection.md`
  - Updated `doc/dev/gitlab_mcp_collection.md`
  - Updated `examples/README.md` (dispatch inputs type note)
- [ ] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[x]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1343/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1343/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1343/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1343/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1343/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
