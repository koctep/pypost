# Roadmap: PYPOST-1135

## Task Metadata

- **Implementation language**: Python
- **Branch name**: `feature/PYPOST-1135-websocket-environments-and-masking`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1135/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1135/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_websocket_environments_and_masking_repro.py`
- [x] **STEP 4: Development**
  - [x] Connect-time template resolution for URL, query params, headers, and subprotocols in `WebSocketPresenter.handle_connect()`
  - [x] Per-send dynamic template resolution in `WebSocketComposer.send_current_payload()` and `WebSocketSequenceRunner`
  - [x] Inbound frame literal safety invariant (no template evaluation on incoming server frames)
  - [x] Two-tier secret masking: Tier 1 exact replacement on ingestion in `build_stream_entry`, Tier 2 heuristic sanitization on egress (clipboard copy in `StreamDetailPane` and file export in `websocket_stream_export.py`)
  - [x] UI variable hover tooltips and snapshot propagation across `WebSocketConnectionEditor`, `WebSocketComposer`, and `StreamDetailPane`
  - [x] Metric tracking via `MetricsRegistry` for `hidden_value_masks_applied_total{surface="websocket"}`
  - [x] Log sanitization across WebSocket components to prevent credential leakage
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1135/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1135/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1135/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/websocket_environments_templating_and_masking.md`
  - [x] `doc/dev/README.md` (Table of Contents update)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1135/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1135/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1135/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1135/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1135/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/websocket_environments_templating_and_masking.md`
- `doc/dev/README.md`

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID)
