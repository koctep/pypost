# Roadmap: PYPOST-1550

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1550/10-requirements.md`
  - Language: Python
  - Business goal: on a longer response, a value the person revealed stays
    visible after an indent change, and a value they left hidden stays
    hidden, including when the formatted text is applied after background
    work. A newer display is not overwritten by a stale background result
    that finishes late.
  - Which fields start masked, hover, and pointer lookup stay as they are.
    Clearing the body and short-response re-mask stay as already promised.
    Cleanup of leftover reveal choices (PYPOST-1551) stays out of scope.
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1550/20-architecture.md`
  - Both outcomes already hold. `set_indent_size` redisplays a longer
    response with `preserve_reveal_state=True`. The worker completion
    applies spans through `set_masked_spans`, which restores revealed
    paths and leaves hidden paths masked. A late completion whose
    generation differs from `_mask_format_generation` returns before
    `setText` and `set_masked_spans`.
  - Step 3 is N/A — no behavioral change. Step 4 adds a green
    characterization test in
    `tests/test_pypost_1550_medium_indent_preserve.py`. Production
    modules stay as they are.
- [x] **STEP 3: Failing Repro Test**
  - N/A — no behavioral change. An indent change on a longer response
    already redisplays that response with reveal memory kept, so a
    revealed value stays visible and a hidden value stays hidden when
    the background format is applied. A completion whose generation is
    no longer current already returns before it replaces the document.
    Characterization tests belong in Step 4, not here.
- [x] **STEP 4: Development**
  - [x] Characterization tests in
    `tests/test_pypost_1550_medium_indent_preserve.py`.
    A longer response keeps a revealed value visible and a hidden
    value hidden after an indent change finishes in the background.
    A stale generation delivered to the existing completion check
    leaves the newer display and its reveal choices.
    Production modules unchanged.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1550/40-code-cleanup.md`
  - Nothing needed fixing. Characterization test hash unchanged.
    Lint, typecheck, and the characterization file passed.
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1550/50-observability.md`
  - No production edit. Preserve is already
    `response_masking_preserve_reveal_state` plus span restore on the
    current worker completion. A dropped stale completion is already
    `response_masking_worker_stale_result_ignored` with generation
    numbers only.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1550/60-tech-debt.md`
  - No new debt. Production was not changed. The stale test's
    private-slot call is the existing generation check. No new
    ticket. PYPOST-1551 is not re-filed. `doc/` left unchanged.
- [x] **STEP 8: Dev Docs**
  - `doc/dev/hidden_response_fields.md`
  - Sibling characterization bullet for a longer response: an indent
    change that finishes in the background keeps a revealed value
    visible and a hidden value hidden. A stale background result for
    an older generation does not replace a newer display. Production
    unchanged.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1550/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1550/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1550/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1550/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1550/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
