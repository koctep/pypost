# Roadmap: PYPOST-1230

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1230/10-requirements.md`
  - Business goal, user stories, acceptance criteria, scope, and test-waiting contract documented.
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1230/20-architecture.md`
  - Defined the test-only `wait_import()` boundary, combined outcome/idle predicate, bounded
    `process_until()` flow, migration plan, testing strategy, and risks.
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_collection_import_wait_repro.py`
  - Red contract coverage for outcome-plus-idle completion and bounded timeout; the shared
    helper is intentionally absent until Step 4.
- [x] **STEP 4: Development**
  - [x] Added test-only `tests.helpers.collection_import_wait.wait_import()` by extracting the
    existing outcome-plus-idle predicate and bounded `process_until()` wait.
  - [x] Migrated all collection-import UI test call sites and kept the focused repro green without
    changing production code.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1230/40-code-cleanup.md`
  - Simplified the helper repro imports, added focused typing, and documented the test-only API.
  - Validation: `make lint`, `make typecheck`, `make verify-ai-tasks`, and focused Make tests pass.
  - `make analyze` is unavailable because the repository has no `analyze` target.
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1230/50-observability.md`
  - Confirmed no production logs or metrics are warranted for this test-only extraction.
  - Added and covered lazy timeout context (`outcome` and presenter `busy` state) in the shared
    test helper.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1230/60-tech-debt.md` records the completed helper extraction, focused contract
    tests, and known baseline Jira issues.
  - Recorded no production debt, one private test-seam coupling risk, and two low-priority future
    follow-ups for broader helper reuse and a stable idle seam.
  - Recorded existing `PYPOST-1261` and `PYPOST-1262` baseline clusters without creating duplicate
    Jira issues.
  - Validation: `make verify-ai-tasks` and `make lint` pass.
- [x] **STEP 8: Dev Docs**
  - `doc/dev/collection_import.md`
  - Documents the shared test-only `wait_import()` API, combined completion contract, timeout
    behavior, migration pattern, lifecycle boundary, and Make-only contributor validation.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1230/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1230/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1230/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1230/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1230/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
