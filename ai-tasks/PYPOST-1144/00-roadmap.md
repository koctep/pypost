# Roadmap: PYPOST-1144

## Task Metadata

- **Implementation language**: Python (PySide6 / Qt worker layer in `pypost/core/qt/`, UI in `pypost/ui/widgets/websocket/`)
- **Branch name**: `refactor/PYPOST-1144-async-stream-export` *(reference only, do not switch)*

## Step Status

- [/] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1144/10-requirements.md`
- [/] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1144/20-architecture.md`
- [/] **STEP 3: Failing Repro Test**
  - `tests/test_websocket_stream_export_responsiveness.py` (red: synchronous export blocks GUI thread)
- [/] **STEP 4: Development**
  - [x] Added `WebSocketStreamExportWorker` (`QThread`) with GUI-thread stream snapshot
  - [x] Migrated `WebSocketStreamView.export_json` / `export_text` to off-thread worker with busy guard
  - [x] Green tests in `tests/test_websocket_stream_export_responsiveness.py`
  - [x] Updated `tests/test_websocket_stream_view_repro.py` export integration for async completion
- [/] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1144/40-code-cleanup.md`
- [/] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1144/50-observability.md`
- [/] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1144/60-tech-debt.md`
- [/] **STEP 8: Dev Docs**
  - `doc/dev/websocket_message_stream.md` — async export worker section
- [ ] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1144/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1144/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_websocket_stream_export_responsiveness.py`

### STEP 4: Development

- `pypost/core/qt/websocket_stream_export_worker.py`
- `pypost/core/websocket_stream_export.py`
- `pypost/ui/widgets/websocket/stream_view.py`
- `tests/test_websocket_stream_export_responsiveness.py`
- `tests/test_websocket_stream_view_repro.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1144/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1144/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1144/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/websocket_message_stream.md`

### COMMIT

- *(pending — commit prep only)*
