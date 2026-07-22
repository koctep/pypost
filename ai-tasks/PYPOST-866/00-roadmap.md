# Roadmap: PYPOST-866

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_e2e_harness_table_doc.py` — mark set ↔ table
- [x] **STEP 4: Development**
  - [x] Removed unmarked `seed_inventory_doc` row from harness table
  - [x] Documented maintenance process (update table with marks; unit
    guards stay out of table; drift guard in `make test`)
  - [x] Green: `make test PYTEST_ARGS="tests/test_agent_e2e_harness_table_doc.py -v --no-cov"`
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Programming language

Python 3.10+ (`.cursor/lsr/do-python.md`) for any automated sync guard.
Markdown under `doc/dev/` follows `.cursor/lsr/do-markdown.md`.

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-866/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-866/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_e2e_harness_table_doc.py` — red set-equality guard
  (marked modules ↔ harness table in `doc/dev/agent_e2e.md`)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-866/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-866/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-866/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/agent_e2e.md`
- `ai-tasks/PYPOST-866/70-dev-docs.md`
