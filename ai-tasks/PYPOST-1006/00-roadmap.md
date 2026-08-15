# Roadmap: PYPOST-1006

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_collections_import_ui.py` —
    `test_logs_file_invalid_on_parse_failure`,
    `test_logs_file_invalid_on_zero_usable_collections`,
    `test_apply_to_all_prompts_only_once_for_three_conflicts`
    (green as expected: verification debt; production already matches)
  - `tests/test_collection_import.py` —
    `test_keep_both_uses_next_numbered_copy_when_copy_and_copy_2_taken`
    (green as expected: KEEP_BOTH copy name past `(2)`)
- [x] **STEP 4: Development**
  - [x] Confirmed Step 3 locks stay green; no production change
    required — tests already lock both invalid-file `reason`s via
    caplog, 3+ apply-to-all KEEP_BOTH, and KEEP_BOTH copy name past
    `(2)`
  - [x] Broader check: both collection-import modules 43 passed;
    full `make test` hit an unrelated segfault in
    `test_reencrypt_runs_when_confirmed` (out of scope)

- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
  - Documented existing `collection_import_file_invalid` WARNING coverage;
    tests now lock both `reason`s via caplog. No new production logs or
    metrics were added (verification debt).
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (verification/testing debt within the existing Python codebase; no new
language or stack introduced).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1006/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1006/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_collections_import_ui.py` (caplog both invalid-file reasons;
  3+ apply-to-all KEEP_BOTH)
- `tests/test_collection_import.py` (KEEP_BOTH copy name past `(2)`)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1006/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1006/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1006/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/collection_import.md` (Testing seam + Observability: caplog both
  invalid-file reasons, 3+ apply-to-all KEEP_BOTH, KEEP_BOTH copy name past
  `(2)`)

## Suggested branch name

`test/PYPOST-1006-collection-import-test-gaps`
