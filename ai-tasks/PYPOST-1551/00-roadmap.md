# Roadmap: PYPOST-1551

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1551/10-requirements.md`
  - Language: Python
  - Business goal: after the masked fields of the current response are
    applied, a reveal choice for a field that is no longer among those
    fields is forgotten. A choice for a field that is still present stays,
    including across an indent refresh of the same response.
  - Clearing the body still forgets every choice. A different response
    still starts masked. Which fields start masked, hover, and pointer
    lookup stay as they are.
  - PYPOST-1549 and PYPOST-1550 stay as already promised. This ticket
    does not expand into those tests. The parent called the outcome
    nice-to-have. It is in this sprint, so it is in scope here.
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1551/20-architecture.md`
  - `set_masked_spans` does not drop `_reveal_state` keys. It restores
    a path stored as true and leaves every other key in the map.
    `_apply_persisted_reveals` only reads the map.
  - Step 3 is a red test before the production prune. The prune drops
    keys whose paths are absent from the spans just applied. A path
    still present keeps its bool. Indent preserve, clear, and a stale
    generation stay as they are. PYPOST-1549 and PYPOST-1550 stay out.
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_pypost_1551_forget_absent_reveal.py`
  - Red on current code: a reveal stored for `token` is restored when
    that field returns to the applied spans. `password` stays revealed
    and `session` stays hidden, including across indent.
- [x] **STEP 4: Development**
  - [x] In `set_masked_spans`, after spans are bound and before restore,
    drop `_reveal_state` keys whose paths are absent from the non-empty
    paths just applied. A path still on that span set keeps its stored
    bool. Indent preserve, `clear`, and the stale-generation return stay
    as they are.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1551/40-code-cleanup.md`
  - Nothing needed fixing. Drop lines and test hash unchanged.
    Lint, typecheck, and the forget-absent test passed.
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1551/50-observability.md`
  - No new log and no metric. DEBUG
    `response_masking_spans_updated` already logs `memory_size` after
    the absent-key drop in `set_masked_spans`. Production was not
    edited.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1551/60-tech-debt.md`
  - No new debt. A false choice for a field that left is also
    dropped, and that drop is intended. No follow-up. PYPOST-1549
    and PYPOST-1550 are not re-filed. `doc/` was left unchanged.
- [x] **STEP 8: Dev Docs**
  - `doc/dev/hidden_response_fields.md`
  - Characterization note beside PYPOST-1549 and PYPOST-1550: a field
    that left starts masked if it comes back; a field still present
    keeps its choice.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1551/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1551/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1551/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1551/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1551/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/hidden_response_fields.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and
  commit hash are reported in chat only, never written to this file.
