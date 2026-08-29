# Roadmap: PYPOST-1104

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1104/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1104/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_mcp_server_headers_table.py`
- [x] **STEP 4: Development**
  - [x] Implemented McpServerHeadersTable with RFC 7230 key validation, template syntax / undefined variable validation, and inline {{ VAR }} autocompletion popup
  - [x] Integrated McpServerHeadersTable into _McpServerEditor with dynamic environment binding and save validation
  - [x] Verified all tests pass green in tests/test_mcp_server_headers_table.py and tests/test_mcp_servers_dialog.py
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1104/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1104/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1104/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - `doc/dev/mcp_server_headers_editor.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1104/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1104/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1104/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1104/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1104/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_server_headers_editor.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
