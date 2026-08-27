# Roadmap: PYPOST-1195

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1195/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1195/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - Confirm red: `tests/test_tabs_presenter.py::TestWebsocketDraftObservability::test_save_tabs_state_logs_omitted_websocket_draft_id`
  - Confirm red: `tests/test_tabs_presenter.py::TestWebsocketDraftObservability::test_save_tabs_state_logs_persisted_saved_websocket_id`
  - Failure mode: stale `websocket_open_tabs_filter` substring vs emit `open_tabs_filter` (per-id events OK; filter assert fails)
- [x] **STEP 4: Development**
  - [x] Aligned filter caplog substrings to `open_tabs_filter` + `persisted_mcp_count=0`
  - [x] Targeted `make test … -k WebsocketDraftObservability` green
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1195/40-code-cleanup.md`
  - `make lint` OK
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1195/50-observability.md` — no new emits; contract realigned
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1195/60-tech-debt.md` — no blockers
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/logging.md` — `open_tabs_filter` + `persisted_mcp_count`
  - Updated `doc/dev/websocket_draft_tab.md` — matching event table
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1195/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1195/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1195/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1195/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1195/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
