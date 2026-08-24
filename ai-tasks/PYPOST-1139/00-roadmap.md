# Roadmap: PYPOST-1139

## Task Metadata

- **Implementation language**: Python
- **Branch name**: *[recorded by the commit procedure — reference only, do not switch]*

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Gather requirements from Jira PYPOST-1139 and PYPOST-1129 TD-1 follow-up
  - [x] Document business goals (multi-client targeting, connection-churn resource reclamation)
  - [x] Define user stories, scope boundaries, and Definition of Done
  - [x] Record implementation language (Python) in task metadata
  - [x] `ai-tasks/PYPOST-1139/10-requirements.md`
- [/] **STEP 2: High-Level Architecture Design**
  - [x] System module diagram and API contracts for `send_to_client` and disconnect cleanup
  - [x] `ai-tasks/PYPOST-1139/20-architecture.md`
- [/] **STEP 3: Failing Repro Test**
  - [x] Red tests: `test_send_to_client_selective_delivery`, `test_disconnect_invokes_delete_later`
- [/] **STEP 4: Development**
  - [x] Add `send_to_client` and `deleteLater()` disconnect cleanup
- [/] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1139/40-code-cleanup.md`
- [/] **STEP 6: Observability**
  - [x] Harness debug log `ws_server_targeted_message_sent`
  - [x] `ai-tasks/PYPOST-1139/50-observability.md`
- [/] **STEP 7: Technical Debt Analysis**
  - [x] TD-1 closed; `ai-tasks/PYPOST-1139/60-tech-debt.md`
- [/] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/websocket_test_harness.md` with `send_to_client` API
- [ ] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1139/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1139/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1139/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1139/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1139/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID)
