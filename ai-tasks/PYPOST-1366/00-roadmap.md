# Roadmap: PYPOST-1366

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1366/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1366/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_websocket_stream_view_folding.py`
- [x] **STEP 4: Development**
  - [x] Iteration 1: Replaced `QTextEdit` with `FoldableCodeView` in `StreamDetailPane`.
  - Added Fold All / Unfold All toolbar actions and widget IDs.
  - Implemented auto-detection of JSON/YAML/XML payloads via `detect_body_format`.
  - Added gutter mouse double-click support in `FoldableCodeView` and `LineNumberArea`.
  - Maintained folding state preservation across word-wrap toggles and hex-mode suppression.
  - Verified 9/9 green tests in `tests/test_websocket_stream_view_folding.py` and
    regression test suites.
  - Passed `make lint` and `make typecheck` quality gates.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1366/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1366/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1366/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - `doc/dev/websocket_stream_view_code_folding.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (see the gate below)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1366/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1366/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1366/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1366/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1366/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/websocket_stream_view_code_folding.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
