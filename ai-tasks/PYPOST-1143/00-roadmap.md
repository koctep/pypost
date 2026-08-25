# Roadmap: PYPOST-1143

## Task Metadata

- **Implementation language**: Python (PySide6 / Qt presenter layer in `pypost/`)
- **Branch name**: `refactor/PYPOST-1143-presenter-env-properties` *(reference only, do not switch)*

## Step Status

- [/] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1143/10-requirements.md`
- [/] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1143/20-architecture.md`
- [/] **STEP 3: Failing Repro Test**
  - `tests/test_websocket_presenter_env_properties.py` (red: missing public `env_vars` / `hidden_keys` properties)
- [/] **STEP 4: Development**
  - [x] Added read-only `env_vars` and `hidden_keys` properties on `WebSocketPresenter`
  - [x] Replaced `getattr(presenter, "_env_vars")` / `getattr(presenter, "_hidden_keys")` in `WebSocketComposer` and `WebSocketStreamView`
  - [x] Green tests in `tests/test_websocket_presenter_env_properties.py`
- [/] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1143/40-code-cleanup.md`
- [/] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1143/50-observability.md`
- [/] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1143/60-tech-debt.md`
- [/] **STEP 8: Dev Docs**
  - `doc/dev/websocket_environments_templating_and_masking.md` — public presenter properties
- [ ] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1143/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1143/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_websocket_presenter_env_properties.py`

### STEP 4: Development

- `pypost/ui/presenters/websocket_presenter.py`
- `pypost/ui/widgets/websocket/composer.py`
- `pypost/ui/widgets/websocket/stream_view.py`
- `tests/test_websocket_presenter_env_properties.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1143/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1143/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1143/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/websocket_environments_templating_and_masking.md`

### COMMIT

- *(pending — commit prep only)*
