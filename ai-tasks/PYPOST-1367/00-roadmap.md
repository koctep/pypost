# Roadmap: PYPOST-1367

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1367/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1367/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_mcp_result_view_folding.py`
- [x] **STEP 4: Development**
  - [x] Defined widget IDs `MCP_CLIENT_RESULT_FOLD_ALL_BUTTON` and
    `MCP_CLIENT_RESULT_UNFOLD_ALL_BUTTON` in `pypost/ui/widget_ids.py`
  - [x] Replaced `QPlainTextEdit` with `FoldableCodeView` in `McpResultView`
    (`pypost/ui/widgets/mcp_client/mcp_result_view.py`)
  - [x] Added "Fold All" and "Unfold All" action buttons to `McpResultView` header row
  - [x] Implemented format detection (`detect_body_format`), dynamic JSON pretty-printing, and fold
    button enable/disable state
  - [x] Exposed `fold_controller()`, `body_format()`, `fold_all()`, and `unfold_all()` delegation
    methods on `McpResultView`
  - [x] Verified 8/8 tests pass in `tests/test_mcp_result_view_folding.py` alongside regression
    suites
  - [x] Verified static analysis via `make lint` and `make typecheck`
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1367/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1367/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1367/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - `doc/dev/mcp_result_view_code_folding.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (see the gate below)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1367/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1367/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1367/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1367/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1367/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
