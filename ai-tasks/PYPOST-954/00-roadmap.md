# Roadmap: PYPOST-954

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *N/A — helper refactor; import contract red until Step 4*
- [x] **STEP 4: Development**
  - [x] Shared `tests/helpers/packaging_doc_lock.py`; refactored both doc-lock modules; helper unit + import contract tests
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (pytest contract helpers); English Markdown in `doc/dev/testing.md`.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-954/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-954/20-architecture.md`

### STEP 3: Failing Repro

- Import contract in `tests/test_packaging_doc_lock_helper.py` (N/A red on
  tokens — helper extraction, not doc semantics)

### STEP 4: Development

- `tests/helpers/packaging_doc_lock.py`
- `tests/test_packaging_doc_lock_helper.py`
- `tests/test_ui_actions_mcp_packaging_doc.py` (refactor)
- `tests/test_agent_e2e_broader_packaging_doc.py` (refactor)

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-954/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-954/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-954/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md` § Packaging doc lock strategy (PYPOST-954)
