# Roadmap: PYPOST-857

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Implemented `pypost/fixtures/agent_e2e_seed.py`
    (inventory constants, builders, `write_agent_e2e_seed`)
  - [x] Added `tests/helpers/agent_e2e_seed.py` and
    `tests/test_agent_e2e_seed.py` (identity + model/item proof, isolation)
  - [x] Documented inventory in `doc/dev/agent_e2e_seed.md`; updated
    `agent_e2e_env.md` / `agent_e2e.md`; listed seed module under
    `make test-agent-e2e`
- [x] **STEP 4: Code Cleanup**
  - [x] `make lint` clean; seed tests pass with module timeout
  - [x] Related env-pack status table lines ≤100 columns
  - [x] `ai-tasks/PYPOST-857/40-code-cleanup.md`
- [x] **STEP 5: Observability**
  - [x] Seed write: `agent_e2e_seed_completed` / `agent_e2e_seed_failed`
  - [x] `ai-tasks/PYPOST-857/50-observability.md`
- [x] **STEP 6: Review and Technical Debt**
  - [x] `ai-tasks/PYPOST-857/60-tech-debt.md` (SAFE TO CLOSE)
- [x] **STEP 7: Dev Docs**
  - [x] `doc/dev/agent_e2e_seed.md` (full template)
  - [x] Logging catalog: `agent_e2e_seed_completed` / `_failed`
  - [x] `ai-tasks/PYPOST-857/70-dev-docs.md`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (`.cursor/lsr/do-python.md`) for seeded workspace fixture pack and
verification tests. Seed inventory documentation under `doc/dev/` follows
Markdown guidelines (`.cursor/lsr/do-markdown.md`).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-857/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-857/20-architecture.md`
- FR8 proof strategy corrected for selection-scoped `ui_snapshot`
  (identity + model/items and/or drive-then-snapshot; present vs active env)

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-857/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-857/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-857/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/agent_e2e_seed.md`
- `doc/dev/logging.md` (catalog entries)
- `ai-tasks/PYPOST-857/70-dev-docs.md`
