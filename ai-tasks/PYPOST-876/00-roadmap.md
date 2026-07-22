# Roadmap: PYPOST-876

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_e2e_failure_artifacts.py::test_dump_propagates_unexpected_exception`
- [x] **STEP 4: Development**
  - [x] Narrowed `_DUMP_BEST_EFFORT_ERRORS` in `agent_e2e_failure.py`
  - [x] Green: `test_dump_propagates_unexpected_exception` + best-effort RuntimeError
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (agent e2e failure dump helpers). Guides: `.cursor/lsr/do-python.md`,
`.cursor/lsr/do-testing.md`. Developer docs in English Markdown
(`.cursor/lsr/do-markdown.md`).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-876/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-876/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_e2e_failure_artifacts.py::test_dump_propagates_unexpected_exception`

### STEP 4: Development

- `pypost/fixtures/agent_e2e_failure.py`
- `tests/test_agent_e2e_failure_artifacts.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-876/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-876/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-876/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/agent_e2e_failure_artifacts.md`
- `doc/dev/logging.md`
- `ai-tasks/PYPOST-876/70-dev-docs.md`
