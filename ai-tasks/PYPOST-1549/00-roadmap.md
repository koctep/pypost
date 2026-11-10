# Roadmap: PYPOST-1549

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1549/10-requirements.md`
  - Language: Python
  - Business goal: after a person reveals a masked value, clearing the
    response body forgets that reveal, and the next body starts masked.
    Hiding that value again, then reformatting the same response for
    indent, leaves it hidden. A value left revealed stays visible.
  - Which fields start masked stays the same. Background reformat of a
    longer response (PYPOST-1550) and leftover reveal cleanup
    (PYPOST-1551) stay out of scope. Hover feedback and how the viewer
    finds a value under the pointer stay as they are.
  - Acceptance gate passed.
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1549/20-architecture.md`
  - Step 3 is N/A — no behavioral change. `clear_body` already discards
    reveal memory, and a re-mask is already stored as false so indent
    reformat leaves that field masked. Step 4 adds characterization
    tests in `tests/test_pypost_1549_clear_and_remask.py`, green on
    current code. Production modules stay as they are.
- [x] **STEP 3: Failing Repro Test**
  - N/A — no behavioral change. `ResponseView.clear_body` already
    discards reveal memory via `ResponseMaskController.clear`, so the
    next body starts masked even when the text matches. A re-mask is
    already stored as false, so an indent reformat of the same response
    leaves that field masked; a value left revealed stays visible; a
    value never revealed stays masked.
- [x] **STEP 4: Development**
  - [x] Characterization tests in
    `tests/test_pypost_1549_clear_and_remask.py`: clear forgets a
    reveal so the next matching body starts masked; a re-mask then
    indent leaves that value hidden, a left-revealed value visible,
    and a never-revealed value masked. Production code unchanged.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1549/40-code-cleanup.md`
  - No cleanup edits. `make lint` clean (test-lint baseline 408, flake8
    on `pypost/`, user-doc checks). `make typecheck` mypy baseline OK
    (175 known errors). Characterization file passed. Production
    unchanged.
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1549/50-observability.md`
  - No production edit. Existing DEBUG events cover clear-reset
    (`reveal_state_cleared` from `clear_body` via `clear`, then
    `response_masking_spans_updated` with `restored_reveals=0`) and
    re-mask persistence (`click_to_reveal_toggle` with
    `revealed=False`, `response_masking_preserve_reveal_state`,
    `reveal_state_spans_cleared`, `response_masking_spans_updated`).
    No new logs or metrics.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1549/60-tech-debt.md`
  - No new debt. Characterization tests only; production unchanged.
    Module timeout is 60. Follow-up tasks: none. PYPOST-1550 and
    PYPOST-1551 already exist and stayed out of scope. User docs are
    not factually wrong about clear-body or re-mask, so `doc/` stays.
    Left `[/]` for the acceptance gate.
- [x] **STEP 8: Dev Docs**
  - `doc/dev/hidden_response_fields.md` — characterization note for
    `tests/test_pypost_1549_clear_and_remask.py`. Clearing the body forgets
    a reveal, so the next matching body starts masked. Re-mask then indent
    leaves that value hidden. A left-revealed value stays visible. A value
    never revealed stays masked.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1549/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1549/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1549/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1549/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1549/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/hidden_response_fields.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
