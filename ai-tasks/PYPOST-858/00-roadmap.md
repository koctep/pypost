# Roadmap: PYPOST-858

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Registered `agent_e2e` marker in `pyproject.toml`
  - [x] Added `tests/_pytest_plugins/agent_e2e.py` fixtures
    (`agent_e2e_session`, `seeded_agent_e2e_session` via `seeded_agent_dirs`)
  - [x] Migrated single-session harness tests onto fixtures; kept
    multi-session isolation on direct `AgentAppSession`
  - [x] `make test-agent-e2e` selects `-m "agent_e2e and not slow"`;
    file-list override via `PYTEST_ARGS` documented
  - [x] Documented marker + fixtures in `agent_e2e.md` / env status
  - [x] Verified: `make test-agent-e2e` → 31 passed
- [x] **STEP 4: Code Cleanup**
  - [x] `40-code-cleanup.md`; flake8 W391 on conftest; lint + 31 tests
- [x] **STEP 5: Observability**
  - [x] `agent_e2e_fixture_ready mode=blank|seeded`; `50-observability.md`
- [x] **STEP 6: Review and Technical Debt**
  - [x] `60-tech-debt.md` — SAFE TO CLOSE; 3 Low Debt follow-ups listed
- [x] **STEP 7: Dev Docs**
  - [x] `70-dev-docs.md`; logging catalog + seed/GUI cross-links


## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (`.cursor/lsr/do-python.md`) for the shared pytest fixture, marker
registration, and migration of agent e2e tests. Developer documentation under
`doc/dev/` follows Markdown guidelines (`.cursor/lsr/do-markdown.md`).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-858/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-858/20-architecture.md`
- Function-scoped blank + seeded fixtures (not pytest session scope)
- Marker registration + make `-m agent_e2e` with file-list override
- Plugin module via `pytest_plugins`; absorb PYPOST-854 marker overlap

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-858/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-858/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-858/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-858/70-dev-docs.md`
- `doc/dev/` updates (umbrella, seed, logging, GUI)
