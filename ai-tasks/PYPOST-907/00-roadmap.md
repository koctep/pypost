# Roadmap: PYPOST-907

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_e2e_ci_double_run_doc.py` (PYPOST-907 evidence + DEFER lock; red on missing docs)
- [x] **STEP 4: Development**
  - [x] Decision **DEFER** after CI duration evidence (no workflow change)
  - [x] Documented evidence table + ENABLE threshold in `doc/dev`
  - [x] Lock test green (2 passed)
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

CI workflow (YAML) and Python pytest contract/doc guards
(`.cursor/lsr/do-python.md`, `.cursor/lsr/do-testing.md`). Developer
documentation in English Markdown (`.cursor/lsr/do-markdown.md`).

## Decision

**DEFER** CI cost trim after reviewing Actions duration evidence (see
`20-architecture.md`). Workflow selection unchanged; docs + lock updated for
evidence review and ENABLE threshold.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-907/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-907/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_e2e_ci_double_run_doc.py`

### STEP 4: Development

- Docs: `doc/dev/testing.md`, `doc/dev/agent_e2e.md`
- Lock green under targeted pytest

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-907/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-907/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-907/60-tech-debt.md`

### STEP 8: Dev Docs

- `ai-tasks/PYPOST-907/70-dev-docs.md`
- Updates under `doc/dev/`
