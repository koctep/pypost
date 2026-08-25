# Roadmap: PYPOST-1157

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1157/10-requirements.md`
  - Implementation language recorded: Python
  - Scope: blank-tab protocol picker on `Ctrl+N` and tab-bar **+** only
    (HTTP Request default; cancel creates no tab; source + protocol telemetry)
  - Review gap 1 fix: confirming **WebSocket** opens a WebSocket blank tab
    (placeholder OK); full editor remains PYPOST-1158
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1157/20-architecture.md`
  - Option A popup `QMenu` (`NewTabProtocolPicker`); HTTP Request first/default
  - `TabsPresenter.open_blank_tab(protocol, source)` is the single routing API
  - WS confirm → `add_blank_websocket_tab()` (`WebSocketTab` placeholder; not `RequestTab`)
  - Failing-repro design: `tests/test_tabs_presenter.py::TestHandleNewTabProtocolPicker`
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_tabs_presenter.py::TestHandleNewTabProtocolPicker`
  - `tests/test_new_tab_protocol_picker.py::TestNewTabProtocolPicker`
  - Red confirmed (no production changes): picker not invoked before editor;
    cancel still creates a tab; WS confirm opens `RequestTab`; `open_blank_tab`
    missing; picker module missing
- [x] **STEP 4: Development**
  - [x] Implemented `NewTabProtocolPicker` (`TabProtocol`, HTTP-first `QMenu`, `setActiveAction`)
  - [x] `handle_new_tab` prompts then `open_blank_tab`; WS confirm uses `add_blank_websocket_tab` (not `open_websocket_tab`)
  - [x] Injectable `protocol_picker`; plus-click / golden e2e inject HTTP so `QMenu.exec()` does not hang
  - [x] Metrics `track_gui_new_tab_action(source, protocol=...)`; cancel emits no metric
  - [x] Step 3 tests green; `make lint` pass; `make test` 272 passed / 0 failed / 1 skipped
  - `tabs_presenter.py` 741 LOC (cap 785)
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1157/40-code-cleanup.md`
  - `make lint` pass; `make analyze` not a target
  - Dead Step 3 scaffolding removed; `tabs_presenter.py` 740 LOC (cap 785)
  - `make test` 272 passed / 0 failed / 1 skipped
  - Snapshot regen `ai-tasks/PYPOST-376/baseline-metrics.md` (this-task LOC drift)
  - Flaky note: `test_presenter_connect_and_disconnect_lifecycle` (not skipped)
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1157/50-observability.md`
  - Added INFO `new_tab_action_cancelled` / `new_tab_action_completed`
    (reused `new_tab_action_triggered` + `gui_new_tab_actions_total`)
  - Operator doc: `doc/prometheus_monitoring.md` now lists `source` + `protocol`
  - Tests: `test_handle_new_tab_cancel_logs_source_without_metric`,
    `test_handle_new_tab_confirm_logs_source_and_protocol`
  - Snapshot regen `ai-tasks/PYPOST-376/baseline-metrics.md` (746 LOC)
  - `tabs_presenter.py` 746 LOC (cap 785)
  - `make lint` pass; `make test` 272 passed / 0 failed / 1 skipped
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1157/60-tech-debt.md`
  - No AC-breaking debt; no missing timeout markers (not a BLOCKER)
  - Shortcuts: injectable picker (no live `QMenu.exec` in CI); WS placeholder;
    close-last-tab HTTP-only; collections `protocol=unknown`
  - Follow-ups: flaky WS lifecycle test (unticketed); collections import hang
    (unticketed); PYPOST-1178; scope PYPOST-1158 / 1159 / 1163 / 1165
  - `tabs_presenter.py` 746 / 785; user docs left to PYPOST-1163
  - No Jira created (Phase D); STEP 7 left `[/]` for acceptance gate
- [x] **STEP 8: Dev Docs**
  - `doc/dev/new_tab_protocol_picker.md` (new focused page)
  - Updated `doc/dev/request_actions.md` (`handle_new_tab`, metric labels)
  - Updated `doc/dev/websocket_ui_client.md` (WS-TM-1 shipped)
  - Updated `doc/dev/ui_identity.md` (`pypost_new_tab_protocol_menu`)
  - Updated `doc/dev/logging.md` (`new_tab_action_cancelled` / `_completed`)
  - Pointers: README, mcp_integration, collection_tree_actions, hotkeys,
    presenter_architecture, agent_golden_e2e
  - User docs left to PYPOST-1163
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1157/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1157/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_tabs_presenter.py::TestHandleNewTabProtocolPicker`
- `tests/test_new_tab_protocol_picker.py::TestNewTabProtocolPicker`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1157/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1157/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1157/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/new_tab_protocol_picker.md`
- `doc/dev/request_actions.md`
- `doc/dev/websocket_ui_client.md`
- `doc/dev/ui_identity.md`
- `doc/dev/logging.md`
- `doc/dev/README.md`
- `doc/dev/mcp_integration.md`
- `doc/dev/collection_tree_actions.md`
- `doc/dev/hotkeys.md`
- `doc/dev/presenter_architecture.md`
- `doc/dev/agent_golden_e2e.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
