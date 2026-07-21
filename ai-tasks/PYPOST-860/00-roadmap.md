# Roadmap: PYPOST-860

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Helper `pypost/fixtures/agent_e2e_failure.py` (dump + paths)
  - [x] `pytest_runtest_makereport` hook in agent_e2e plugin
  - [x] Tests: write/mask/best-effort/hook subprocess
  - [x] `.gitignore` `artifacts/`; docs + env-contract status
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (`.cursor/lsr/do-python.md`); pytest hooks/fixtures; Markdown docs
(`.cursor/lsr/do-markdown.md`).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-860/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-860/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-860/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-860/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-860/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/agent_e2e_failure_artifacts.md` (+ cross-links)
- `ai-tasks/PYPOST-860/70-dev-docs.md`
