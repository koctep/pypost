# Roadmap: PYPOST-873

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_e2e_ci_double_run_doc.py` (doc/workflow DEFER lock; red on missing docs)
- [x] **STEP 4: Development**
  - [x] Decision **DEFER** — no workflow selection change
  - [x] Documented intentional 3.11 double-run + revisit criteria
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

YAML workflow contract + Python pytest doc/workflow guards; developer docs in
English Markdown. Guides: `.cursor/lsr/do-python.md`,
`.cursor/lsr/do-testing.md`, `.cursor/lsr/do-markdown.md`.

## Decision

**DEFER** CI cost trim. Keep dual coverage until minutes / double-failure
pain justify ENABLE (see `20-architecture.md` and `doc/dev/testing.md`).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-873/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-873/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_e2e_ci_double_run_doc.py`

### STEP 4: Development

- Docs: `doc/dev/testing.md`, `doc/dev/agent_e2e.md`, `doc/dev/setup.md`
- Lock green under targeted pytest

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-873/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-873/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-873/60-tech-debt.md`

### STEP 8: Dev Docs

- `ai-tasks/PYPOST-873/70-dev-docs.md`
- Updates under `doc/dev/`
