# Roadmap: PYPOST-424

## Task language

- **Programming language for implementation**: Python (see `10-requirements.md`).

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
  - Team Lead review: **approved** (2025-03-27); see **Team Lead (PYPOST-424)** below.
- [x] **STEP 3: Development**
  - [x] Added `Request Timeout (seconds)` row to `SettingsDialog` form layout (after
    indent rows, before MCP); load/save unchanged.
  - [x] Tests: `tests/test_settings_dialog.py` (layout visibility, load, accept);
    extended `test_save_then_load_roundtrip` for `request_timeout`.
  - [x] `scripts/test.sh`: 292 passed; `scripts/lint.sh` on touched files: clean;
    `scripts/check-line-length.sh` on touched files: clean.
  - [x] **Senior Engineer review** (STEP 3 inner loop): see **Senior Engineer (PYPOST-424)** below.
- [x] **STEP 4: Code Cleanup**
  - [x] `scripts/check-line-length.sh`, `scripts/lint.sh` on PYPOST-424 files: clean.
  - [x] `scripts/test.sh`: 292 passed; targeted settings tests: 11 passed.
  - [x] Artifact: `ai-tasks/PYPOST-424/40-code-cleanup.md`.
  - [x] No code edits required; validation-only cleanup for scoped files.
- [x] **STEP 5: Observability**
  - [x] `settings_applied` INFO includes `request_timeout` (seconds) after successful save/apply;
    no duplicate signals from layout-only change; artifact `50-observability.md`.
  - [x] Verification: `scripts/test.sh`; `scripts/lint.sh` / `scripts/check-line-length.sh` on
    touched files.
- [x] **STEP 6: Review and Technical Debt**
  - [x] Artifact: `ai-tasks/PYPOST-424/60-review.md` (delivered scope, debt, risk,
    tests, follow-ups).
  - [x] Checkpoint (2025-03-27): Technical review complete; no release blockers;
    user approval of STEP 6 before STEP 7.
- [x] **STEP 7: Dev Docs**
  - [x] Artifact: `ai-tasks/PYPOST-424/70-dev-docs.md` (operator/dev usage, save/load,
    verification commands, observability/troubleshooting).
  - [x] **Finalization (2025-03-27)**: Developer documentation complete; PYPOST-424 ready for
    user closure/review (no commit in this STEP 7 invocation).

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-424/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-424/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-424/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-424/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-424/60-review.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-424/70-dev-docs.md`

## PM status

| Field | Value |
| ----- | ----- |
| Task | PYPOST-424 |
| Current step | **STEP 7** complete; **user closure/review** of task and `70-dev-docs.md` |
| Status | Developer docs delivered; roadmap updated for finalization |
| Next action | User confirms task closure in Jira or requests follow-up |
| Notes | STEP 7 artifact: `70-dev-docs.md`. Full chain: requirements through `60-review.md`. |

### Team Lead (PYPOST-424)

- **Architecture review** (2025-03-27): `20-architecture.md` aligned with `10-requirements.md`
  (FR-1–FR-5, NFRs, acceptance criteria). Research matches code: `timeout_spin` wired but missing
  from `QFormLayout` in `settings_dialog.py`.
- **Adjustments**: Added explicit requirements traceability and clarified placement against the
  current form row order in `20-architecture.md`.
- **Verdict**: **Approved** — proceed to STEP 3 (development).

### Senior Engineer (PYPOST-424)

- **STEP 3 code review** (2025-03-27): Verified `settings_dialog.py` adds a single
  `form_layout.addRow` for `timeout_spin` after indent rows and before MCP (matches
  `20-architecture.md` placement). Load (`setValue` from `AppSettings`) and save
  (`accept()` → `request_timeout`) unchanged and consistent with FR-3/FR-4. No
  duplicate or alternate `request_timeout` widgets in the codebase.
- **Tests**: `tests/test_settings_dialog.py` asserts widget on layout, load, and
  accept path; `tests/test_settings_persistence.py` round-trip includes
  `request_timeout`. Full `scripts/test.sh`: 292 passed; line-length check clean
  on touched files.
- **Verdict**: **STEP 3 approved** for **user review gate** (no STEP 4+ artifacts
  in this checkpoint).

- **STEP 5 observability** (2025-03-27): Extended `settings_applied` INFO in
  `main_window.py` with `request_timeout` so post-save logs match persisted timeout after the
  visible control (STEP 3). No new metrics; single success log line unchanged in cardinality.
  Documented troubleshooting and signal distinction in `50-observability.md`.

### Product Owner (PYPOST-424)

- **PO review complete** (2025-03-27): Requirements validated for business
  alignment, scope, and user-facing completeness. Ready for STEP 2 architecture.

## Recommended Branch Name

- `fix/PYPOST-424-show-request-timeout-control`
