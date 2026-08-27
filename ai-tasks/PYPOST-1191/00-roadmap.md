# Roadmap: PYPOST-1191

## Task Metadata

- **Issue**: PYPOST-1191
- **Title**: [PYPOST-1158] Reuse one WebSocketRegistry per save_tabs_state/close_tab
- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1191/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1191/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - Added regression test asserting single registry construction
- [x] **STEP 4: Development**
  - Implemented `make_websocket_saved_predicate` and `make_mcp_client_saved_predicate` and wired into presenter operations
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1191/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1191/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1191/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - Updated developer documentation / docstrings
- [x] **COMMIT: Commit Changes**
