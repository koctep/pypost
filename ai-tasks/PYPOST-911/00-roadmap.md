# Roadmap: PYPOST-911

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_e2e_ci_failure_artifacts_ui_proof_doc.py` (doc lock; red then green)
- [x] **STEP 4: Development**
  - [x] Decision **DEFER** live Artifacts UI screenshot — procedure + checklist in docs
  - [x] Notes stub `live-proof-notes.md`; lock green (2 passed; 874/909/910 still green)
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python pytest doc guards + English Markdown developer docs.
Guides: `.cursor/lsr/do-python.md`, `.cursor/lsr/do-testing.md`,
`.cursor/lsr/do-markdown.md`. No application runtime change.

## Decision

**DEFER** live Artifacts UI screenshot / notes from a real failing run —
no public Actions run currently exposes downloadable
`agent-e2e-failure-artifacts` (or matrix twin). Lock a maintainer how-to
+ capture checklist in `doc/dev` and a notes stub under this task folder.
See `20-architecture.md`.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-911/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-911/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_e2e_ci_failure_artifacts_ui_proof_doc.py`

### STEP 4: Development

- Docs: `doc/dev/agent_e2e_failure_artifacts.md`, `agent_e2e.md`,
  `testing.md`
- Notes stub: `ai-tasks/PYPOST-911/live-proof-notes.md`
- Lock green under targeted pytest

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-911/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-911/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-911/60-tech-debt.md`

### STEP 8: Dev Docs

- `ai-tasks/PYPOST-911/70-dev-docs.md`
- Updates under `doc/dev/`
