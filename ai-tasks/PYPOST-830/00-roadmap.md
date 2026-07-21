# Roadmap: PYPOST-830

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Removed module-local `setUpClass`/`QApplication` from the three
    gateway TestCase modules; request shared `qapp` via
    `@pytest.mark.usefixtures("qapp")` (collection, environment, H3 stress)
  - [x] Verified: focused gateway modules 15/15; with responsiveness 20/20;
    full `make test` 1701 passed (3 unrelated SOLID LOC baseline failures)
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**
  - [x] Documented `usefixtures("qapp")` for gateway `TestCase` modules in
    `doc/dev/gui_testing.md` (plus cross-links in `testing.md` /
    `environment_storage_async.md`)
  - [x] Artifact: `ai-tasks/PYPOST-830/70-dev-docs.md`

## Programming language

Python 3.10+ (`.cursor/lsr/do-python.md`)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-830/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-830/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-830/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-830/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-830/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/gui_testing.md`
- `doc/dev/testing.md`
- `doc/dev/environment_storage_async.md`
- `ai-tasks/PYPOST-830/70-dev-docs.md`

## Suggested branch name

`chore/PYPOST-830-align-gateway-tests-qapp`
