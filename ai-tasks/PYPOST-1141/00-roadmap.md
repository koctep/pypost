# Roadmap: PYPOST-1141

## Task Metadata

- **Implementation language**: Python
- **Branch name**: *[recorded by the commit procedure — reference only, do not switch]*

## Step Status

- [/] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1141/10-requirements.md`
- [/] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1141/20-architecture.md`
- [/] **STEP 3: Failing Repro Test**
  - `tests/test_websocket_batch_eviction_repro.py`
- [/] **STEP 4: Development**
  - Added `BatchEvictionPlan` and `calculate_batch_evictions` / `apply_batch_evictions` on `MessageStream`
  - Refactored `StreamListModel.append_batch` to use public `MessageStream` batch APIs
  - Green tests in `tests/test_websocket_batch_eviction_repro.py`
- [/] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1141/40-code-cleanup.md`
- [/] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1141/50-observability.md`
- [/] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1141/60-tech-debt.md`
- [/] **STEP 8: Dev Docs**
  - Updated `doc/dev/websocket_message_stream.md`
- [ ] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1141/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1141/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_websocket_batch_eviction_repro.py`

### STEP 4: Development

- `pypost/core/websocket_stream.py`
- `pypost/ui/widgets/websocket/stream_model.py`
- `tests/test_websocket_batch_eviction_repro.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1141/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1141/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1141/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/websocket_message_stream.md`

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID)
