# Roadmap: PYPOST-423

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
  - Team lead review complete — see **Team lead (STEP 2)** below.
- [x] **STEP 3: Development**
  - [x] Added `parse_retryable_status_codes` and `RetryableCodesValidationFailure` in
    `pypost/models/retry.py` (comma-separated tokens, 100–599, reject empty segments).
  - [x] `SettingsDialog.accept()` validates before `super().accept()`; shows
    `QMessageBox.warning` and returns on failure (no `new_settings`, dialog stays open).
  - [x] Unit tests: `tests/test_retryable_status_codes_parse.py`.
  - [x] Tests run: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest`
    `tests/test_retryable_status_codes_parse.py` `tests/test_retry.py`
    `tests/test_settings_persistence.py` `tests/test_apply_settings_font.py` — **49 passed**.
  - [x] **Senior engineer review (STEP 3 inner loop)** — see **Senior engineer (STEP 3)** below.
- [x] **STEP 4: Code Cleanup**
  - [x] flake8 + line-length check on `retry.py`, `settings_dialog.py`,
    `test_retryable_status_codes_parse.py` — clean.
  - [x] Pytest regression suite (49 tests) — **49 passed**.
  - [x] Artifact: `ai-tasks/PYPOST-423/40-code-cleanup.md`.
  - [x] **STEP 4 complete** — no code edits required; validations documented in
    `40-code-cleanup.md`.
- [x] **STEP 5: Observability**
  - [x] Structured WARNING on blocked save: `retryable_codes_settings_validation_failed`
    with `reason=` only (no raw user input); distinct from HTTP retry logs.
  - [x] Artifact: `ai-tasks/PYPOST-423/50-observability.md`.
  - [x] **STEP 5 complete** — ready for user review before STEP 6.
- [x] **STEP 6: Review and Technical Debt**
  - [x] Artifact: `ai-tasks/PYPOST-423/60-review.md` (delivered scope, debt, risks, tests,
    follow-ups; **no release blockers**).
  - [x] **STEP 6 complete** — checkpoint: technical review recorded; ready for user review
    before STEP 7 (dev docs).
- [x] **STEP 7: Dev Docs**
  - [x] Artifact: `ai-tasks/PYPOST-423/70-dev-docs.md` (API, save UX, tests, observability,
    troubleshooting).
  - [x] **STEP 7 complete** — developer-facing notes finalized; **ready for user closure /
    review** (PYPOST-423 scope only; no commit in this step).

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming language (STEP 1)

- **Python** — implementation is expected in the existing PyPost UI codebase (`pypost` package).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-423/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-423/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-423/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-423/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-423/60-review.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-423/70-dev-docs.md`

## PM status

- **Task:** PYPOST-423 — `[PYPOST-402] retryable_codes_edit silently drops invalid input`
- **STEP 1:** Completed — requirements captured in `10-requirements.md`.
- **Product owner review:** Complete — business logic and scope reviewed; requirements
  updated with clarifications where needed. **STEP 1 is approved for STEP 2 (architecture).**
- **STEP 2:** Complete — architecture approved by team lead (see **Team lead (STEP 2)**).
- **STEP 3:** Completed — parse/validate helper, settings save guard, unit tests (see STEP 3
  bullets below). Senior engineer STEP 3 approved.
- **STEP 4:** Completed — lint/line-length/tests documented in `40-code-cleanup.md`; no source
  edits required.
- **STEP 5:** Completed — settings validation failure logging documented in
  `50-observability.md`; code change in `settings_dialog.py`.
- **STEP 6:** Completed — technical review in `60-review.md` (no blocker debt; low risk; tests
  adequate for agreed scope).
- **STEP 7:** Completed — `70-dev-docs.md` captures developer changes, save behavior, commands,
  and observability/troubleshooting. **Finalization:** Task documentation complete; user may
  close or archive PYPOST-423 after review.

## Senior engineer (STEP 3)

- **Status:** Code and test review complete (PYPOST-423 scope only).
- **Verdict:** **Approved for user review gate** — implementation matches `10-requirements.md`
  FR-1–FR-5 / AC-1–AC-3 and `20-architecture.md`: no silent token dropping; validation runs on
  save; failures show `QMessageBox.warning` and block `super().accept()` (dialog remains open,
  no `new_settings`); empty segments, non-numeric tokens, and out-of-range codes fail with
  structured reasons; valid comma-separated lists and empty/whitespace input behave as
  designed; regression suite passes (49 tests) and line length check clean for touched files.
- **Notes:** No code changes required from this review. STEP 4+ artifacts not started.

## Team lead (STEP 2)

- **Status:** Architecture review complete (PYPOST-423 scope only).
- **Verdict:** **Approved** — `20-architecture.md` matches `10-requirements.md` (FR-1–FR-5,
  AC-1–AC-3). Refined: explicit **empty comma segment** rule (empty tokens after split =
  validation failure) and a **requirements mapping** table for traceability.
- **Notes:** No rework required. Implementation may proceed under STEP 3 with the documented
  helper + `SettingsDialog.accept()` guard + unit tests; observability per STEP 5 as
  already outlined.

## Product owner (STEP 1)

- **Status:** Review complete (PYPOST-423 scope only).
- **Notes:** Requirements stay free of implementation and architecture; Python language
  choice for later steps is unchanged.

## Recommended Branch Name

- `fix/PYPOST-423-validate-retryable-codes-input`
