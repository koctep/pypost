# Roadmap: PYPOST-1066

## Task Metadata

- **Implementation language**: Python
- **Branch name**: `test/PYPOST-1066-cover-clean-mypy-boundaries`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1066/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1066/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] N/A — no honest red repro exists: runtime validation confirmed that empty current and
    empty baseline inputs produce no differences, while zero current errors against a non-empty
    baseline produces resolved-debt diagnostics and exit code 1 without ordinary success output.
    The missing work is passing regression coverage for Step 4, not a production behavior change.
- [x] **STEP 4: Development**
  - [x] Added a focused `_diff_errors([], [])` regression test that verifies both returned
    difference lists are empty.
  - [x] Added a hermetic `main()` regression test for zero current errors against a non-empty
    version-2 baseline. It verifies exit code 1, resolved-debt diagnostics and counts, and the
    absence of new-error and ordinary-success output.
  - [x] Focused validation passed: the exact two test node IDs passed via `make test` (2 passed),
    and `.venv/bin/python -m flake8 tests/test_mypy_baseline.py` reported no findings. The module
    retains `pytestmark = pytest.mark.timeout(30)` for both tests.
  - [x] Full `make test`: 2,341 passed, 3 failed, and 23 deselected. All three failures reproduced
    unchanged at base commit `04db6e383002a359e5866e6bed9698cec91ee821` and are NON-BLOCKER —
    pre-existing: the PYPOST-1077 artifact and SOLID snapshot failures are tracked by PYPOST-1111;
    the qapp-alignment failure is tracked by PYPOST-1110. Step 7 must also record them in
    `60-tech-debt.md`.
- [x] **STEP 5: Code Cleanup**
  - [x] `make lint` passed. The repository has no `make analyze` target, so the documented
    `lint` target was used as the closest Makefile static-analysis target.
  - [x] Direct flake8 and syntax checks passed for `tests/test_mypy_baseline.py`; no formatting,
    import, line-length, debug-print, conflict-marker, or whitespace cleanup was needed.
  - [x] Both focused regression tests passed via `make test` (2 passed), and the module-level
    `pytestmark = pytest.mark.timeout(30)` explicitly covers both tests.
  - [x] `git diff --check` passed.
  - [x] `make typecheck` was also run and reported unrelated baseline drift in unchanged
    production files: 9 new error occurrences and 2 resolved entries (219 baseline versus 226
    current). PYPOST-1066 changes tests only, so no out-of-scope baseline update was made.
  - `ai-tasks/PYPOST-1066/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1066/50-observability.md`
  - Production logging and metrics are N/A because PYPOST-1066 changes regression tests only; the
    command's stdout/stderr diagnostics and exit status already form the observable contract.
  - Focused validation passed: both boundary tests passed via `make test` (2 passed), including
    assertions for resolved-debt diagnostics, baseline/current counts, absence of false success or
    new-error output, and exit status `1`.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1066/60-tech-debt.md`
  - No new in-scope debt or timeout blocker was found; both added tests inherit the explicit
    module-level 30-second timeout and contain no internal waits.
  - The three full-suite failures reproduced at base commit
    `04db6e383002a359e5866e6bed9698cec91ee821` and remain NON-BLOCKER — pre-existing:
    PYPOST-1111 owns the PYPOST-1077 artifact and SOLID snapshot failures, and PYPOST-1110 owns the
    qapp-alignment failure.
  - Existing `make typecheck` baseline drift is owned by active sprint issue PYPOST-1086; no
    duplicate follow-up was created.
  - Documentation updates are N/A for this test-only technical-debt step; Step 8 retains its own
    developer-documentation assessment.
  - Focused validation passed (2 tests), `make lint` passed, direct Markdown and relative-link
    checks passed for the Step 7 artifact and roadmap, and diff hygiene passed.
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/static_type_checking.md` with the maintained clean-boundary contract:
    clean-to-clean passes without differences, while a clean current run against a stale
    non-empty baseline reports resolved entries and counts, exits non-zero, and requires an
    explicit baseline update.
  - Preserved and verified the guide's quality-gate scope: `make typecheck` is optional and is not
    included in `make check` or the current CI workflow.
  - Validation passed: `make lint-docs`; direct relative-link checks for the updated guide and
    roadmap; `git diff --check`; 100-character line-length checks; and both focused mypy-baseline
    boundary tests via `make test` (2 passed).
- [x] **COMMIT: Commit Changes**
  - Primary commit: `bb2757f1` — `test(typecheck): PYPOST-1066 cover clean baseline boundaries`
  - Working branch: `dev`; suggested branch: `test/PYPOST-1066-cover-clean-mypy-boundaries`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1066/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1066/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1066/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1066/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1066/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- `bb2757f1` — `test(typecheck): PYPOST-1066 cover clean baseline boundaries`
- Metadata closure recorded in a follow-up Conventional Commit on `dev`.
