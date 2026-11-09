# Roadmap: PYPOST-1392

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1392/10-requirements.md`
  - Language: Python
  - Business goal: keep user-chosen reveal/mask choices across indent reformat and tab-driven re-renders
  - Acceptance: reviewed externally (prior Steps 1–4 gate)
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1392/20-architecture.md`
  - Path-keyed `_reveal_state` on controller; preserve flag on indent re-display
  - Failing-repro plan: `tests/test_pypost_1392_failing_repro.py`
  - Acceptance: reviewed externally (prior Steps 1–4 gate)
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_pypost_1392_failing_repro.py::test_reveal_state_preserved_across_indent_reformat`
  - Confirmed red: indent reformat resets all spans to masked (intended defect)
  - Acceptance: reviewed externally (prior Steps 1–4 gate)
- [x] **STEP 4: Development**
  - [x] Path-keyed `_reveal_state` on `ResponseMaskController` + `clear_spans()`
  - [x] `display_response(..., preserve_reveal_state=)` + `set_indent_size` preserves
  - [x] Step 3 repro green; added `test_reveal_state_resets_on_new_response`
  - Production: `pypost/ui/widgets/response_mask_controller.py`, `response_view.py`
  - Acceptance: reviewed externally (prior Steps 1–4 gate)
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1392/40-code-cleanup.md`
  - `make lint` + `make typecheck` clean; targeted masking tests green
  - Acceptance: reviewed externally (Steps 5–8 + blocker gate)
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1392/50-observability.md`
  - DEBUG: preserve / clear_spans / clear / restore counts (no secrets)
  - Acceptance: reviewed externally (Steps 5–8 + blocker gate)
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1392/60-tech-debt.md`
  - Debt filed: PYPOST-1549 (TD-1), PYPOST-1550 (TD-2), PYPOST-1551 (TD-3)
  - Acceptance: reviewed externally (SAFE TO CLOSE)
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/hidden_response_fields.md` (reveal-state preservation)
  - Note in `doc/dev/response_mask_worker.md` for async restore
  - Acceptance: reviewed externally (Steps 5–8 + blocker gate)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1392/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1392/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1392/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1392/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1392/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
