# Roadmap: PYPOST-884

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_collection_storage_worker_qapp_alignment.py`
    (source guard: usefixtures qapp; no setUpClass QApplication)
- [x] **STEP 4: Development**
  - [x] Removed module-local `setUpClass`/`QApplication` from
    `tests/test_collection_storage_worker.py`; request shared `qapp` via
    `@pytest.mark.usefixtures("qapp")`
  - [x] Verified: alignment + worker + collection gateway **7 passed**
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
  - [x] Verdict: SAFE TO CLOSE; unticketed follow-ups: none
- [x] **STEP 8: Dev Docs**
  - [x] Documented worker `usefixtures("qapp")` in `doc/dev/gui_testing.md`
    (plus cross-links in `testing.md` / `environment_storage_async.md`)
  - [x] Artifact: `ai-tasks/PYPOST-884/70-dev-docs.md`

## Programming language

Python 3.10+ (`.cursor/lsr/do-python.md`)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-884/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-884/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_collection_storage_worker_qapp_alignment.py`

### STEP 4: Development

- `tests/test_collection_storage_worker.py`
- `tests/test_collection_storage_worker_qapp_alignment.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-884/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-884/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-884/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/gui_testing.md`
- `doc/dev/testing.md`
- `doc/dev/environment_storage_async.md`
- `ai-tasks/PYPOST-884/70-dev-docs.md`

## Suggested branch name

`chore/PYPOST-884-align-collection-worker-qapp`
