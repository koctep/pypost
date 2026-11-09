# Roadmap: PYPOST-1535

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1535/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1535/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - Existing red tests in `tests/test_mcp_server_impl.py`:
    - `TestMCPServerImpl::test_register_tools_keeps_only_exposed_and_normalizes_names`
    - `TestMCPServerImpl::test_call_tool_invokes_request_service_with_mcp_context`
    - `TestMCPServerImpl::test_call_tool_applies_mcp_param_defaults_when_args_omitted`
    - `TestMCPServerImpl::test_call_tool_honors_explicit_custom_pagination_args`
  - Focused repro: `make test PYTEST_ARGS='tests/test_mcp_server_impl.py -k "register_tools_keeps or call_tool_invokes_request_service or call_tool_applies_mcp_param or call_tool_honors_explicit" --tb=short'`
- [x] **STEP 4: Development**
  - [x] Iteration 1: Keep atomic `tools_map` swap in `MCPServerImpl.register_tools`; stop deep-copying registered tools so caller identity is preserved; focused + full `tests/test_mcp_server_impl.py` green
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1535/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1535/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1535/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/mcp_process_isolation.md` (register_tools identity + atomic swap)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1535/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1535/20-architecture.md`

### STEP 3: Failing Repro

- Automated red tests under `tests/test_mcp_server_impl.py` (identity `assertIs` cases)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1535/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1535/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1535/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_process_isolation.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
