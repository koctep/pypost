# Roadmap: PYPOST-1365

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1365/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1365/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_response_view_folding.py`
- [x] **STEP 4: Development**
  - [x] Implemented `detect_body_format` (`format_detector.py`) for Content-Type
    and payload sniffing (JSON, YAML, XML, PLAIN)
  - [x] Enhanced `FoldController` with `collapse_all()` / `fold_all()`,
    `unfold_all()`, `reveal_block()`, and `ensure_scanned()`
  - [x] Implemented `FoldableCodeView` (`foldable_code_view.py`) subclassing
    `QPlainTextEdit` with `LineNumberArea` gutter and folding chevrons
  - [x] Integrated `FoldableCodeView` into `ResponseView` with format detection,
    JSON syntax highlighting, search reveal, context menu folding actions,
    and Fold All / Unfold All toolbar buttons
  - [x] Verified Step 3 repro tests (`tests/test_response_view_folding.py`),
    search, context menu, and editor test suites pass green
  - [x] Verified code quality: `make lint` and `make typecheck` pass cleanly with
    line limits <= 100 chars
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1365/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1365/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1365/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/response_view_code_folding.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (see the gate below)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1365/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1365/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1365/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1365/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1365/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
