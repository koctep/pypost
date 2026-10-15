# Roadmap: PYPOST-1370

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1370/00-roadmap.md`
  - [x] `ai-tasks/PYPOST-1370/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1370/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_background_fold_scanner.py`
- [x] **STEP 4: Development**
  - [x] Create `FoldScanWorker` in `pypost/ui/widgets/fold/fold_worker.py`
  - [x] Implement pure text-based fold parsing with `scan_text(text, body_format)` in `structure_scanner.py`
  - [x] Refactor `FoldController` to subclass `QObject`, handle `LARGE_DOCUMENT_THRESHOLD_BYTES = 500 * 1024`, emit `scan_finished`, and manage background workers
  - [x] Verify green repro test `tests/test_background_fold_scanner.py` and quality gates
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1370/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1370/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1370/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/background_folding_scanner.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1370/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1370/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1370/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1370/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1370/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/background_folding_scanner.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
