# Roadmap: PYPOST-833

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Exposed `MainWindow.is_ui_ready` after startup restore gate
  - [x] Extracted shared `compose_app` / `ComposedApp` from `main.py`
  - [x] Added `pypost.agent.lifecycle.AgentAppSession` (offscreen, temp dirs,
    ephemeral metrics, processEvents ready wait, clean shutdown)
  - [x] Added `tests/test_agent_lifecycle_smoke.py` and `doc/dev/agent_lifecycle.md`
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
  - [x] Structured lifecycle logs: launch, ready, timeout, shutdown
  - [x] `main_window_ui_ready` on production ready gate
  - [x] `ai-tasks/PYPOST-833/50-observability.md`
- [x] **STEP 6: Review and Technical Debt**
  - [x] `ai-tasks/PYPOST-833/60-tech-debt.md` (non-blocking follow-ups; SAFE TO CLOSE)
- [x] **STEP 7: Dev Docs**
  - [x] Polished `doc/dev/agent_lifecycle.md` (API, config, troubleshooting)
  - [x] Catalogued `agent_session_*` / `main_window_ui_ready` in `doc/dev/logging.md`
  - [x] `ai-tasks/PYPOST-833/70-dev-docs.md`

## Programming language

Python (`.cursor/lsr/do-python.md`)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-833/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-833/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-833/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-833/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-833/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/agent_lifecycle.md`
- `doc/dev/logging.md` (agent lifecycle events)
- `ai-tasks/PYPOST-833/70-dev-docs.md`
