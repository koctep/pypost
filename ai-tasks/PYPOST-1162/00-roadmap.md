# Roadmap: PYPOST-1162

## Task Metadata

- **Implementation language**: Python — PyPost desktop client and automated tests

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1162/10-requirements.md` — context-aware WebSocket hotkeys (WS-TM-6)
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1162/20-architecture.md` — tab-kind routing, main_window registration, red-test plan
- [x] **STEP 3: Failing Repro Test**
  - Red: `tests/test_main_window_hotkeys.py` — WS tab Ctrl+S save, F5 connect, Ctrl+L focus URL, SECTION_ORDER, request-editor no-op on WS tab
- [x] **STEP 4: Development**
  - [x] Iteration: `tabs_presenter_hotkeys.py` + TabsPresenter delegates
  - [x] Iteration: `main_window._setup_shortcuts` WebSocket Session section
  - [x] Iteration: `hotkeys.py` SECTION_ORDER + composer format JSON
  - Tests green via targeted `make test`
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1162/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1162/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1162/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - `doc/dev/websocket_hotkeys.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1162/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1162/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_main_window_hotkeys.py`

### STEP 4: Development

- `pypost/ui/presenters/tabs_presenter_hotkeys.py`
- `pypost/ui/main_window.py`, `pypost/ui/hotkeys.py`
- `pypost/ui/widgets/websocket/composer.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1162/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1162/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1162/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/websocket_hotkeys.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above.
