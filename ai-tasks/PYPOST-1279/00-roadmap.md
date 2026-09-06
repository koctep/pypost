# Roadmap: PYPOST-1279

## Task Metadata

- **Implementation language**: Python
- **Jira**: [PYPOST-1279](https://pypost.atlassian.net/browse/PYPOST-1279)
- **Summary**: Support importing collections from file and from connected library

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1279/10-requirements.md` — business requirements, scope, acceptance criteria,
    and resolved assumptions
  - Independent review accepted the business-focused requirements and safety rules.
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1279/20-architecture.md` — source adapter, Copy/Link persistence,
    selector flow, safety/thread boundaries, and Step 3 repro plan
  - Review gap fixes specified concrete resolver/link-refresh seams and per-item failure behavior.
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_collection_import_library_pypost_1279_repro.py` — red repros for source dispatch,
    registered/cloned entry projection, Copy/Link persistence, path safety, conflicts, and
    cancellation.
  - Independent review accepted the deterministic, timeout-marked test coverage.
- [x] **STEP 4: Development**
  - Implemented the Qt-free library import service, safe manifest resolution, Copy/Link
    materialization, shared conflict planning, and persistence-failure accounting.
  - Added separate From File and From Library UI routes with asynchronous listing/resolution,
    Copy/Link selection, cancellation handling, and linked-collection refresh.
  - Focused validation passes through the required Make test, lint, and typecheck targets.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1279/40-code-cleanup.md` records lint, type, timeout, and cleanup checks.
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1279/50-observability.md` documents structured logs and bounded import metrics.
  - Independent observability review accepted the implementation and validation evidence.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1279/60-tech-debt.md` records task trade-offs and exact pre-existing baseline
    failures from the complete `make check`.
  - Independent technical-debt review accepted the artifact.
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/collection_import.md` with the PYPOST-1279 library-import architecture,
    API, Copy/Link semantics, safety rules, telemetry, and troubleshooting.
  - Independent documentation review accepted the corrected wording and links.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1279/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1279/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1279/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1279/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1279/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to a file.
