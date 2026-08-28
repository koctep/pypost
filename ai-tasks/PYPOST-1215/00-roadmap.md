# Roadmap: PYPOST-1215

## Task Metadata

- **Implementation language**: Python (repro harness) + Markdown (evidence baseline)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1215/10-requirements.md` drafted
  - Requirements, user stories, acceptance criteria, boundaries, entities, and non-goals documented
  - Step 1 left in progress `[/]` pending acceptance gate review
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1215/20-architecture.md` drafted
  - High-level design for reproducible flake evidence capture (parallel vs isolated profiles)
  - Repro harness architecture, baseline evidence schema, and Make-only execution commands defined
  - Red test strategy for Step 3 specified (repro execution under parallel load vs isolated pass)
  - Scope boundaries and non-goals enforced (no root-cause diagnosis, no production fixes)
- [x] **STEP 3: Failing Repro Test**
  - Empirical repro runs: isolated baseline vs parallel load execution
  - Artifact: `ai-tasks/PYPOST-1215/25-failing-repro.md`
- [x] **STEP 4: Development**
  - [x] Created canonical baseline evidence deliverable in
    `ai-tasks/PYPOST-1215/baseline-evidence.md` documenting environment metadata, Make-only
    differential invocation recipes, empirical run matrix, observed concurrency contention
    profiles, behavioral lock validation, and handoff contracts for DIAG-1 (PYPOST-1216)
    and FIX-1 (PYPOST-1217)
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1215/40-code-cleanup.md` created
  - Validated markdown hygiene, line length <= 100 chars, and relative link correctness
  - Verified static analysis and artifact gates via `make lint` and `make verify-ai-tasks`
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1215/50-observability.md` created
  - Documented structured test runner logging (INFO, NOTICE, ERROR) and UI action DEBUG logs
  - Documented differential duration metrics across isolated node (1.35s) vs parallel suite (8.14s)
  - Documented timeout parameters (test 60s, worker 120s) and monitoring integration
  - Step 6 left in progress `[/]` pending acceptance gate review
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1215/60-tech-debt.md` created
  - Documented shortcuts taken (Make-only execution, sampled matrix, deferred root-cause diagnosis)
  - Verified no production code touched and pytest timeout marker compliance on `tests/test_ui_actions.py`
  - Documented +40.3% parallel duration inflation and high-concurrency worker timeout risks
  - Documented downstream handoffs for DIAG-1 (PYPOST-1216) and FIX-1 (PYPOST-1217)
  - Step 7 left in progress `[/]` pending acceptance gate review
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/testing.md` to document completed baseline evidence deliverable in `ai-tasks/PYPOST-1215/baseline-evidence.md`
  - Documented Make-only differential execution profiles (isolated node pass vs multi-worker parallel suite duration inflation +40.3%) for downstream DIAG-1 (PYPOST-1216) and FIX-1 (PYPOST-1217)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1215/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1215/20-architecture.md`

### STEP 3: Failing Repro

- `ai-tasks/PYPOST-1215/25-failing-repro.md`
- Target test: `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises`

### STEP 4: Development

- `ai-tasks/PYPOST-1215/baseline-evidence.md`
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1215/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1215/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1215/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/testing.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
