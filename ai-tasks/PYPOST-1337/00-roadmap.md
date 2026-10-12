# Roadmap: PYPOST-1337

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Artifact: `ai-tasks/PYPOST-1337/10-requirements.md`.
  - Documented trustworthy distinction between valid type analysis, unavailable diagnostics,
    known debt, and justified baseline reconciliation.
  - Existing evidence: live gate reports zero current findings against 181 known entries;
    isolated base `36d7782b` reproduces checker exit 1. Root cause remains uninvestigated.
  - Current task base: `103fe81a`; no baseline deletion or code/test repair performed in Step 1.
  - Requirements complete for independent review; STEP 1 remains `[/]` until acceptance.
- [x] **STEP 2: High-Level Architecture Design**
  - Artifact: `ai-tasks/PYPOST-1337/20-architecture.md`.
  - Investigated root cause of 0-error report: unhandled non-zero exit codes with empty parsed errors (e.g. missing mypy module, fatal error exit code >= 2).
  - Designed fail-closed validation in check_mypy_baseline before diffing or writing baseline.
  - Designed mandatory failing repro test plan for Step 3.
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_mypy_baseline.py::TestMypyBaselineExecutionIntegrity`
- [x] **STEP 4: Development**
  - [x] Implemented fail-closed execution validation in `scripts/check_mypy_baseline.py` (handling returncode >= 2 and returncode != 0 with empty parsed errors, protecting `--update-baseline` and baseline diffing). Verified all repro tests pass.
- [x] **STEP 5: Code Cleanup**
  - Artifact: `ai-tasks/PYPOST-1337/40-code-cleanup.md`.
  - Static analysis, line length, formatting, and test suites verified cleanly.
- [x] **STEP 6: Observability**
  - Artifact: `ai-tasks/PYPOST-1337/50-observability.md`.
  - Assessed observability for `scripts/check_mypy_baseline.py` CLI utility.
  - Diagnostic execution failure output directed to stderr; status summaries to stdout. Metrics N/A.
- [x] **STEP 7: Technical Debt Analysis**
  - Artifact: `ai-tasks/PYPOST-1337/60-tech-debt.md`.
  - Analyzed shortcuts, test bounds, and classified pre-existing test failures under tracked issues (PYPOST-1363, PYPOST-1361).
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/static_type_checking.md` with fail-closed execution validation rules, `--update-baseline` corruption protection, and environment troubleshooting.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1337/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1337/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1337/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1337/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1337/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
