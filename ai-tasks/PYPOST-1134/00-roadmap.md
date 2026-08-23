# Roadmap: PYPOST-1134

## Task Metadata

- **Implementation language**: Python
- **Branch name**: `feature/PYPOST-1134-composer-presets-sequences`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1134/10-requirements.md` (created)
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1134/20-architecture.md` (created)
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_websocket_composer_and_sequence_repro.py` (created)
- [x] **STEP 4: Development**
  - [x] Implemented WS-6 features:
    - [x] Added `WS_COMPOSER_*`, `WS_PRESET_*`, `WS_SEQUENCE_*`, `WS_MESSAGES_TAB` widget IDs in `pypost/ui/widget_ids.py`
    - [x] Pure planning and validation engine `pypost/core/websocket_sequence.py`
    - [x] Async Qt sequence runner `pypost/core/qt/websocket_sequence_runner.py`
    - [x] Multi-format composer widget `pypost/ui/widgets/websocket/composer.py`
    - [x] Presets and sequences panel `pypost/ui/widgets/websocket/presets_panel.py`
    - [x] Tab and presenter integration in `websocket_tab.py` and `websocket_presenter.py`
    - [x] Extended `tests/test_ui_identity_spotcheck.py` with 25 new identities
    - [x] All 20 tests in `tests/test_websocket_composer_and_sequence_repro.py` GREENsupporting Text, JSON, Hex, Base64 with real-time validation and dispatch controls.
  - [x] Presets & sequences panel: implemented `pypost/ui/widgets/websocket/presets_panel.py` embedded as `Messages` sub-tab in `WS_DETAIL_TABS`.
  - [x] Tab and presenter integration: wired `WebSocketTab` and `WebSocketPresenter` for sequence runner and composer coordination.
  - [x] Test suite verification: all 20 tests in `tests/test_websocket_composer_and_sequence_repro.py`, 5 spotchecks, and 176 total WebSocket tests GREEN with clean linting.
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1134/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1134/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1134/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/websocket_composer_presets_sequences.md`
- [x] **COMMIT: Commit Changes**
  - [x] Commit `348edcbb` — `feat(websocket): PYPOST-1134 message composer, saved presets and sequence runner`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1134/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1134/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1134/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1134/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1134/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/websocket_composer_presets_sequences.md`

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID)
