# Roadmap: PYPOST-1187

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1187/10-requirements.md`
  - Language: Python (hermetic GUI tests for MCP Client Headers)
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1187/20-architecture.md`
  - Verification-debt architecture: extend `test_mcp_client_tab.py`
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_mcp_client_tab.py` —
    `test_headers_table_edit_execute_outbound_forwards_widget_headers`,
    `test_mcp_client_headers_table_hover_masks_hidden_keys`
  - First run: **GREEN** (coverage gap closed; no production defect)
- [x] **STEP 4: Development**
  - [x] Harness-only: green proofs landed; production no-op (FR: no chrome change)
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1187/40-code-cleanup.md`
  - `make lint` OK; full-file tab tests PASSED
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1187/50-observability.md`
  - N/A — no new production logs/metrics
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1187/60-tech-debt.md`
  - No AC-breaking debt; SAFE TO CLOSE after orchestrator review
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/mcp_client_draft_tab.md` (PYPOST-1187 Headers proofs)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1187/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1187/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_mcp_client_tab.py` (two new GUI proofs; green on first run)

### STEP 4: Development

- Source code: none (production no-op)
- Tests: Headers edit → execute_outbound + hover mask
- Documentation updates: Step 8

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1187/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1187/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1187/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_client_draft_tab.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
