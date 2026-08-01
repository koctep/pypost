# Roadmap: PYPOST-908

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_e2e_ci_double_run_doc.py` (PYPOST-908 in both docs;
        red on missing `agent_e2e.md` anchor)
- [x] **STEP 4: Development**
  - [x] Cited existing Actions timing notes (no invented numbers)
  - [x] Cross-linked PYPOST-908 from `testing.md` + `agent_e2e.md`
  - [x] Lock green (2 passed)
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python pytest contract/doc guards (`.cursor/lsr/do-python.md`,
`.cursor/lsr/do-testing.md`). Developer documentation in English Markdown
(`.cursor/lsr/do-markdown.md`). No CI workflow selection change.

## Decision

**Lock published evidence** already recorded by PYPOST-907 in `doc/dev` —
do not invent timings; do not automate capture (defer to PYPOST-931). Satisfy
PYPOST-908 acceptance by making job-duration / overlap notes discoverable
from docs and this task’s artifacts, with a lock that PYPOST-908 stays linked.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-908/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-908/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_e2e_ci_double_run_doc.py`

### STEP 4: Development

- Docs: `doc/dev/testing.md`, `doc/dev/agent_e2e.md`
- Lock green under targeted pytest

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-908/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-908/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-908/60-tech-debt.md`

### STEP 8: Dev Docs

- `ai-tasks/PYPOST-908/70-dev-docs.md`
- Updates under `doc/dev/`
