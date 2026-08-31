# Roadmap: PYPOST-1241

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1241/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1241/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_mypy_baseline_live.py`
- [x] **STEP 4: Development**
  - [x] Iteration 1: Phase 1 — Core Domain & Stream Export Typing (`websocket_stream_export.py`, `websocket_stream_export_worker.py`, `environment_variables_adapter.py`)
  - [x] Iteration 2: Phase 2 — Generic Save Orchestrator Abstractions (`request_save_orchestrator.py`, `websocket_save_orchestrator.py`, `mcp_client_save_orchestrator.py`)
  - [x] Iteration 3: Phase 3 — TabsPresenter Integration (`tabs_presenter.py`: `_index_of_tab`, `_stale_context_*`)
  - [x] Iteration 4: Phase 4 — UI Presenters, Dialog Signatures, and PySide6 / Qt Alignments (`TabClosePromptProtocol`, `tabs_presenter_draft.py`, `tabs_presenter_hotkeys.py`, `collection_tree_actions.py`, `settings_dialog.py`, `library_presenter.py`, `library_dialogs.py`, `InstantPopup`)
  - [x] Iteration 5: Phase 5 — Baseline Update & Gate Verification (`scripts/check_mypy_baseline.py --update-baseline`, `mypy-baseline.json`, verified `make typecheck` and `test_mypy_baseline_live.py` green)
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1241/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1241/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1241/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1241/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1241/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_mypy_baseline_live.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1241/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1241/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1241/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/static_type_checking.md`
- `doc/dev/README.md`
- `doc/dev/websocket_save_flow.md`
- `doc/dev/websocket_message_stream.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
