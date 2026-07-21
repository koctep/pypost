# Roadmap: PYPOST-861

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Extended `test-agent-e2e` help text for env pack
  - [x] Makefile smoke: deps, help, recipe, agent_e2e selection
  - [x] CI job `agent-e2e` runs `make install` + `make test-agent-e2e`
  - [x] Verified: makefile smokes (4) + `make test-agent-e2e` → 32 passed
- [x] **STEP 4: Code Cleanup**
  - [x] `40-code-cleanup.md`; flake8 clean; timeouts present
- [x] **STEP 5: Observability**
  - [x] CI job summary; `50-observability.md`
- [x] **STEP 6: Review and Technical Debt**
  - [x] `60-tech-debt.md` — SAFE TO CLOSE; NEW Debt listed (not created)
- [x] **STEP 7: Dev Docs**
  - [x] `70-dev-docs.md`; agent_e2e / env / testing / setup cross-links

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (`.cursor/lsr/do-python.md`) for Makefile smoke tests and any
pytest/CI glue. Makefile / GitHub Actions YAML for make and CI entry.
Developer documentation under `doc/dev/` follows Markdown guidelines
(`.cursor/lsr/do-markdown.md`).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-861/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-861/20-architecture.md`

### STEP 3: Development

- `Makefile` (`test-agent-e2e` help)
- `.github/workflows/test.yml` (`agent-e2e` job)
- `tests/test_makefile.py` (smokes)

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-861/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-861/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-861/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-861/70-dev-docs.md`
- `doc/dev/agent_e2e.md`, `agent_e2e_env.md`, `testing.md`, `setup.md`
