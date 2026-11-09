# Roadmap: PYPOST-1531

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - N/A — no behavioral change; this task adds coverage of existing event paths.
- [x] **STEP 4: Development**
  - [x] Implemented keyboard coverage in `tests/test_hidden_fields_event_paths.py`: Delete and Backspace remove nonadjacent selected rows, keep remaining order and the trailing blank, and forward `data_changed` and `changed`. Trailing-row deletion and those keys during editing leave the selector row in place.
  - [x] Implemented context-menu coverage by sending `QContextMenuEvent` to the table viewport. The real handler stays in place; only instance `QMenu.exec` is replaced, because Shiboken ignores a class-level patch and would open a blocking menu. Cases cover removal, disabled removal without a selection, cancellation, and Add Selector followed by typing into the real editor and committing.
  - [x] Production modules unchanged. Targeted hidden-field suites and `make lint` passed.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1531/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1531/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1531/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/hidden_fields_table.md` with keyboard and
    context-menu event-path coverage.
    Suite: `tests/test_hidden_fields_event_paths.py`.
    Production behavior unchanged.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1531/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1531/20-architecture.md`

### STEP 3: Failing Repro

- N/A — no behavioral change. The accepted architecture identifies no production defect;
  the task adds event-path coverage for existing keyboard and context-menu behavior.
  No deliberately failing test or production change is needed for this coverage-only step.

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1531/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1531/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1531/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/hidden_fields_table.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
