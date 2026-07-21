# Roadmap: PYPOST-835

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `pypost/agent/ui_snapshot.py` (capture API, walker, roles/values,
    truncation constant `UI_SNAPSHOT_MAX_VALUE_LENGTH`)
  - [x] Added `EnvPresenter.current_hidden_keys` public accessor (pairs with
    `current_variables` for sanitizer context)
  - [x] Exported `capture_ui_snapshot` from `pypost.agent`; added
    `AgentAppSession.ui_snapshot()` convenience
  - [x] Added `tests/test_ui_snapshot.py` (shape/hierarchy, masking, truncation,
    ready integration via `AgentAppSession`)
  - [x] Lint clean; snapshot + identity + lifecycle tests pass
- [x] **STEP 4: Code Cleanup**
  - [x] `make lint` clean; focus files within 100 characters
  - [x] Hoisted `capture_ui_snapshot` import in `lifecycle.py`
  - [x] Typed `EnvPresenter.current_variables` as `dict[str, str]`
  - [x] Snapshot + lifecycle smoke tests pass (6)
  - [x] `ai-tasks/PYPOST-835/40-code-cleanup.md`
- [x] **STEP 5: Observability**
  - [x] DEBUG `ui_snapshot_captured` (node_count, named_count, duration_ms);
    never log tree/values/env
  - [x] CI gate remains `tests/test_ui_snapshot.py` (masking + shape)
  - [x] `ai-tasks/PYPOST-835/50-observability.md`
- [x] **STEP 6: Review and Technical Debt**
  - [x] Honest debt analysis vs architecture / observability / tests
  - [x] `ai-tasks/PYPOST-835/60-tech-debt.md` (no Jira tickets; plain follow-ups)
  - [x] Verdict: SAFE TO CLOSE (non-blocking deferred items only)
- [x] **STEP 7: Dev Docs**
  - [x] `doc/dev/ui_snapshot.md` + TOC / cross-links
  - [x] `doc/dev/logging.md` catalogs `ui_snapshot_captured`
  - [x] `ai-tasks/PYPOST-835/70-dev-docs.md`
  - [x] **ROADMAP FULLY COMPLETE** (all steps `[x]`)

## Programming language

Python (`.cursor/lsr/do-python.md`)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-835/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-835/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-835/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-835/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-835/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/ui_snapshot.md`
- `doc/dev/README.md` (TOC)
- `doc/dev/agent_lifecycle.md`, `ui_identity.md`, `gui_testing.md`, `logging.md`
- `ai-tasks/PYPOST-835/70-dev-docs.md`
