# Roadmap: PYPOST-840

**Programming language:** Python

**Suggested branch:** `refactoring/PYPOST-840-dedupe-wait-until` (reference only)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *N/A — no behavioral change (AC already met by PYPOST-837)*
- [x] **STEP 4: Development**
  - [x] Added regression lock tests for single wait_until implementation
  - [x] Documented PYPOST-840 closure on ui_wait / testing docs
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-840/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-840/20-architecture.md`

### STEP 3: Failing Repro

- N/A — production already satisfies acceptance (see architecture)

### STEP 4: Development

- `tests/test_wait_until_dedup_lock.py`
- Doc cross-links under `doc/dev/`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-840/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-840/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-840/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/ui_wait.md`, `doc/dev/testing.md` (PYPOST-840 notes)
