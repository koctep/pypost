# Roadmap: PYPOST-1140

## Task Metadata

- **Implementation language**: Python (test infrastructure — `tests/websocket_echo_server.py`, PySide6 / Qt WebSockets)
- **Branch name**: *[recorded by the commit procedure — reference only, do not switch]*

## Step Status

- [/] **STEP 1: Requirements Gathering and Documentation**
- [/] **STEP 2: High-Level Architecture Design**
- [/] **STEP 3: Failing Repro Test**
  - [/] `tests/test_websocket_echo_server.py::test_max_history_truncates_received_and_sent_buffers`
- [/] **STEP 4: Development**
  - [/] Added `max_history` constructor parameter and ring-buffer truncation on received/sent buffers
  - [/] Preserved `close_on_message_count` via `_total_received_count` separate from buffer length
- [/] **STEP 5: Code Cleanup**
- [/] **STEP 6: Observability**
- [/] **STEP 7: Technical Debt Analysis**
- [/] **STEP 8: Dev Docs**
- [ ] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1140/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1140/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_websocket_echo_server.py::test_max_history_truncates_received_and_sent_buffers`

### STEP 4: Development

- `tests/websocket_echo_server.py` — `max_history` parameter and buffer truncation

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1140/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1140/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1140/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/websocket_test_harness.md`

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID)
