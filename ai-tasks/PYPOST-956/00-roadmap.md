# Roadmap: PYPOST-956

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  *(completed under sprint-task-runner Step 1 autonomy)*
- [x] **STEP 2: High-Level Architecture Design**
  *(completed under sprint-task-runner Step 2 autonomy)*
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_e2e_response_panel.py` — snapshot Send settle convention lock (`test_shared_send_settle_exports_wait_response_after_snapshot`, `test_snapshot_send_settle_modules_use_shared_helper`)
- [x] **STEP 4: Development**
  - [x] Added `wait_response_after_snapshot` to `tests/helpers/agent_e2e_send_settle.py`
  - [x] Migrated `tests/test_agent_e2e_http_mapping_multi_url.py` — removed `_wait_response`, companion uses shared helper
  - [x] Convention locks green; mapping agent e2e suite green (2 tests)
- [x] **STEP 5: Code Cleanup**
  - [x] `40-code-cleanup.md`; `make lint` + scoped flake8 clean
- [x] **STEP 6: Observability**
  - [x] `50-observability.md` — test-helper only; no new logs
- [x] **STEP 7: Review and Technical Debt**
  - [x] `60-tech-debt.md` — SAFE TO CLOSE
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/agent_e2e_send_settle.md`, `doc/dev/agent_e2e_http.md`; `70-dev-docs.md`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Language

Python 3.10+ (test helper extraction under `tests/helpers/`); Markdown for task
artifacts (`.cursor/lsr/do-markdown.md`).

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-956/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-956/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (convention lock in
  `tests/test_agent_e2e_response_panel.py`)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-956/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-956/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-956/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`
