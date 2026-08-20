# Roadmap: PYPOST-1086

## Task Metadata

- **Implementation language**: Python
- **Suggested branch name**: `fix/PYPOST-1086-clear-qt-mypy-drift`
- **Delivery branch**: `dev` (existing sprint branch; no branch switch performed)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Recorded current `make typecheck` reproduction evidence at base commit `49441bb4`
  - [x] Documented current drift from the older Jira description
  - [x] Created `ai-tasks/PYPOST-1086/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Researched live diagnostics, generic Qt stubs, official signal and thread contracts
  - [x] Designed concrete signal payloads and separated result delivery from thread lifecycle
  - [x] Defined Step 3 red repro, runtime regression coverage, and error handling
  - [x] Defined guarded two-entry baseline reconciliation from 219 to 217 entries
  - [x] Created `ai-tasks/PYPOST-1086/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] Added `tests/test_worker.py::test_request_worker_separates_result_from_qthread_finished`
  - [x] Uses mocked execution, `qapp`, native `QThread.start()`, and bounded Qt/worker waits
  - [x] Exact Makefile node fails red on the inherited `QThread.finished` descriptor assertion
- [x] **STEP 4: Development**
  - [x] Separated response delivery onto `RequestWorker.request_finished` while preserving native
    `QThread.finished` lifecycle cleanup
  - [x] Narrowed Qt signal payload declarations and added boundary validation for nullable or
    dynamically sourced values
  - [x] Made the reviewed red node green and added focused coverage for nullable script errors and
    invalid boundary payloads
  - [x] Verified raw mypy introduced no new diagnostics and resolved exactly the two approved
    baseline records
  - [x] Reconciled the baseline from 219 to 217 records; `make typecheck` passes with 217 current
    and known diagnostics
  - [x] Passed changed-code lint and 178 focused tests covering workers, presenters, save flow,
    import flow, and baseline tooling
  - [x] Ran the full suite: 2,347 passed and 3 unrelated failures, all reproduced at base commit
    `49441bb4`
  - [x] Hardened the missing-snapshot test with a signature-compatible signal slot and added
    focused type-only warning coverage for rejected invalid script-error payloads
- [x] **STEP 5: Code Cleanup**
  - [x] Clarified response signal naming, handler payload types, and native thread lifecycle intent
  - [x] Removed task-created redundant imports without changing runtime behavior
  - [x] Base-classified direct test-file flake8 findings as pre-existing and preserved them
  - [x] Recorded cleanup and proportional validation in `ai-tasks/PYPOST-1086/40-code-cleanup.md`
  - [x] Passed lint, typecheck, byte-compilation, 6 exact/companion nodes, and 179 focused tests
- [x] **STEP 6: Observability**
  - [x] Audited boundary warnings, worker failure signaling, lifecycle logs, and existing metrics
  - [x] Confirmed invalid payload warnings expose type metadata without payload values or secrets
  - [x] Determined new production logs and metrics are N/A because existing coverage is sufficient
  - [x] Added privacy-focused warning assertions and documented the decision in
    `ai-tasks/PYPOST-1086/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Assessed signal design, dynamic boundaries, validation, logging, tests, and lifecycle risk
  - [x] Verified baseline version, scope, count, and exact resolved-record removals
  - [x] Classified direct test-tree style findings as pre-existing non-blockers
  - [x] Verified PYPOST-1110 and PYPOST-1111 ownership and To Do status read-only in Jira
  - [x] Recorded no blocker or unticketed follow-up in
    `ai-tasks/PYPOST-1086/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/static_type_checking.md` to the passing 217-error baseline state
  - [x] Removed stale 219-count wording while preserving the historical 218-error triage snapshot
  - [x] Documented concrete Qt payload types, native thread lifecycle, and safe union boundaries
  - [x] Preserved the optional `make typecheck` and not-in-CI policy
  - [x] Passed Markdown/link checks, repository lint/typecheck, focused tests, and diff checks
- [/] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1086/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1086/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1086/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1086/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1086/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID)
