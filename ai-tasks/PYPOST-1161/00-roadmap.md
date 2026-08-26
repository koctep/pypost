# Roadmap: PYPOST-1161

## Task Metadata

- **Implementation language**: Python — PyPost desktop client and automated tests

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1161/10-requirements.md` — business requirements for WebSocket save-to-collection flow (WS-TM-5); HTTP save flow researched as reference behavior
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1161/20-architecture.md` — WebSocket save orchestrator, tab entry points, signal wiring, failing-repro plan
- [x] **STEP 3: Failing Repro Test**
  - Red: `tests/test_websocket_save_orchestrator.py` — draft save, overwrite, stale cancel, save-as new id
  - Red: `tests/test_tabs_presenter.py::TestWebsocketSaveSignals` — `websocket_saved` / `websocket_save_as_completed` handlers
  - Red: `tests/test_websocket_save_flow_integration.py` — Actions Save + Ctrl+S entry points on `WebSocketTab`
  - Red: `tests/test_collections_presenter.py::test_add_saved_websocket_to_tree_appends_ws_row` — `add_saved_websocket_to_tree`
  - Confirmed: 9 reds via targeted `make test`; all green after Step 4
- [x] **STEP 4: Development**
  - [x] Iteration: `connection_snapshot_from_tab` + `WebSocketSaveOrchestrator`
  - [x] Iteration: `WebSocketTab` Actions / shortcuts / save signals
  - [x] Iteration: TabsPresenter WS save handlers + signals
  - [x] Iteration: `add_saved_websocket_to_tree` + `main_window_signals` wiring
  - Tests green: orchestrator, presenter signals, collections tree, integration
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1161/40-code-cleanup.md` — lint pass, timeout markers verified, no code edits required
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1161/50-observability.md` — documents Step 4 logging/metrics (`ws_save_*`, GUI save counters)
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1161/60-tech-debt.md` — sibling stale-tab gap, dialog labels, follow-ups (no Jira links)
- [x] **STEP 8: Dev Docs**
  - `doc/dev/websocket_save_flow.md` — save pipeline overview, API, tests, troubleshooting
  - `doc/dev/README.md` — TOC entry added
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1161/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1161/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_websocket_save_orchestrator.py` (primary: draft save + overwrite/stale/save-as)
- `tests/test_tabs_presenter.py::TestWebsocketSaveSignals`
- `tests/test_websocket_save_flow_integration.py`
- `tests/test_collections_presenter.py::TestCollectionsPresenter::test_add_saved_websocket_to_tree_appends_ws_row`

### STEP 4: Development

- `pypost/ui/websocket_save_orchestrator.py`
- `pypost/ui/widgets/websocket/websocket_tab.py`
- `pypost/ui/presenters/tabs_presenter.py`
- `pypost/ui/presenters/collections_presenter.py`
- `pypost/ui/main_window_signals.py`
- Tests listed under STEP 3

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1161/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1161/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1161/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/websocket_save_flow.md`
- `doc/dev/README.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
