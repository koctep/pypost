# Roadmap: PYPOST-910

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_e2e_ci_failure_retention_doc.py` (doc/workflow retention lock; red then green)
- [x] **STEP 4: Development**
  - [x] Decision **ENABLE** — `retention-days: 14` on both failure uploads
  - [x] Workflow inputs on `agent-e2e` and `test` matrix
  - [x] Docs updated; lock green (2 passed; 874/909 locks still green)
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

**ENABLE** explicit `retention-days: 14` on agent e2e failure artifact
uploads (jobs `agent-e2e` and main `test` matrix). See
`20-architecture.md` and `doc/dev/agent_e2e_failure_artifacts.md`.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-910/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-910/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_e2e_ci_failure_retention_doc.py`

### STEP 4: Development

- `.github/workflows/test.yml`
- Docs: `doc/dev/agent_e2e_failure_artifacts.md`, `agent_e2e.md`, `testing.md`
- Lock green under targeted pytest

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-910/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-910/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-910/60-tech-debt.md`

### STEP 8: Dev Docs

- `ai-tasks/PYPOST-910/70-dev-docs.md`
- Updates under `doc/dev/`
