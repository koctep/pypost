# Roadmap: PYPOST-1539

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1539/10-requirements.md`
  - Language: Python
  - Business goal: a person writing a field selector is not told a broken
    draft is acceptable just because cleanup collapses an extra dot
  - Done when `users..email` is rejected and `users[*].email` stays
    acceptable
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1539/20-architecture.md`
  - Chosen fix: reject a literal `..` on the stripped path before
    wildcard normalization and the collapse loop in
    `validate_field_selector`
  - Failing-repro plan: `tests/test_pypost_1539_failing_repro.py`
    (module timeout 30; Step 3 writes the red test)
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_pypost_1539_failing_repro.py`
- [x] **STEP 4: Development**
  - [x] Implemented a literal `..` reject on the stripped path in
    `validate_field_selector` before `_normalize_wildcards`, reusing the
    existing unsupported result and leaving the collapse loop in place
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1539/40-code-cleanup.md`
  - `make lint` passed; no lint or 100-character edits in the changed files
  - `tests/test_pypost_1539_failing_repro.py` passed; module timeout 30
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1539/50-observability.md`
  - None added. `validate_field_selector` and the literal `..` reject do
    not log. No log covers the reject path. Production code and tests
    stay unchanged.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1539/60-tech-debt.md`
  - No new debt. The existing unsupported message stays. Specialized
    messages stay with PYPOST-1540. The repro module timeout is present
    coverage.
- [x] **STEP 8: Dev Docs**
  - `doc/dev/hidden_fields_table.md`
  - A written `..` is rejected before wildcard normalization.
    `users..email` is not ok. `users[*].email` stays ok. The existing
    unsupported message is reused.
  - No other developer doc stated that `..` collapses into a valid
    selector. No second guide.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1539/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1539/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_pypost_1539_failing_repro.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1539/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1539/50-observability.md`
- None added. The literal `..` reject does not log. Selector text stays
  out of logs. Production code and tests stay unchanged.

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1539/60-tech-debt.md`
- No new debt. The existing unsupported message stays. Specialized
  messages stay with PYPOST-1540. The repro module timeout is present
  coverage.

### STEP 8: Dev Docs

- `doc/dev/hidden_fields_table.md`
- A written `..` is rejected before wildcard normalization.
  `users..email` is not ok. `users[*].email` stays ok. The existing
  unsupported message is reused.
- No other developer doc stated that `..` collapses into a valid
  selector. No second guide.

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
