# Roadmap: PYPOST-1133

## Task Metadata

- **Implementation language**: Python
- **Branch name**: `feature/PYPOST-1133-stream-inspector`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1133/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1133/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_websocket_stream_view_repro.py`
- [x] **STEP 4: Development**
  - [x] Implementing WebSocket Stream Inspector (stream_view.py, widget IDs, presenter, tab integration)
  - [x] Iteration 1 — Added all WS_STREAM_* widget ID constants to `pypost/ui/widget_ids.py` (16 constants, registered in KEY_WIDGET_IDS)
  - [x] Iteration 2 — Implemented `StreamFilterProxyModel` (delegates to StreamQuery for direction/kind/search/heartbeat filtering), `StreamItemDelegate` (virtualized canvas painter with timestamp, glyph, payload snippet, wire size; uniformItemSizes), and `_format_hex_dump` helper
  - [x] Iteration 3 — Implemented `StreamDetailPane` (metadata header, truncation banner, Copy/Set-as-variable/Wrap/Hex action buttons, QTextEdit payload viewer, variable_capture_requested Signal)
  - [x] Iteration 4 — Implemented `WebSocketStreamView` (filter toolbar with search/direction/kind/heartbeat controls, pause/clear/export buttons, match-count label, drop-notice banner, QListView with proxy model, empty-filter overlay with clear-filter button, follow-tail badge, StreamDetailPane splitter pane)
  - [x] Iteration 5 — Integrated `WebSocketStreamView` into `WebSocketTab` replacing bare QListView; wired export actions to `websocket_stream_export.py`; extended `tests/test_ui_identity_spotcheck.py` with all WS_STREAM_* ids
  - [x] Fixed flake8 lint errors: added missing `MessageStream` import, broke long lines (E501), fixed E203 whitespace in slice, removed unused `QListView` and `WS_STREAM_VIEW` imports from `websocket_tab.py`
  - [x] All 17 repro tests GREEN; all 5 spotcheck tests GREEN; all 154 websocket tests GREEN; make lint PASSES
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1133/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1133/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1133/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/websocket_stream_inspector.md`
- [x] **COMMIT: Commit Changes**
  - [x] Commit `d14ab80f` — `feat(websocket): PYPOST-1133 virtualized stream inspector, filtering and detail pane`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1133/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1133/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1133/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1133/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1133/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/websocket_stream_inspector.md`

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID)
