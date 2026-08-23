# Roadmap: PYPOST-1136

## Task Metadata

- **Implementation language**: Python
- **Branch name**: dev

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1136/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1136/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_websocket_settings_and_limits_repro.py`
- [x] **STEP 4: Development**
  - [x] Iteration 1: Extend `AppSettings` model in `pypost/models/settings.py` with `ws_*` fields, validation, and defaults
  - [x] Iteration 2: Implement thread-safe `SessionSlots`, `SlotAcquireResult`, and coordinator helpers in `pypost/core/websocket_session_policy.py`
  - [x] Iteration 3: Register 9 Prometheus & OTel metrics in `MetricsRegistry`, `MetricsOTel`, and `MetricsProtocol`, with dynamic delegation in `MetricsManager`
  - [x] Iteration 4: Integrate `SessionSlots` and structured zero-leak logging into `WebSocketPresenter` in `pypost/ui/presenters/websocket_presenter.py`
  - [x] Iteration 5: Implement `WebSocketSettingsSection` in `pypost/ui/widgets/settings/websocket_section.py` and wire into `SettingsDialog`
  - [x] Iteration 6: Verified all 14 tests in `tests/test_websocket_settings_and_limits_repro.py` pass (GREEN), all 211 `tests/test_websocket*.py` pass, baseline audit, flake8, and mypy baseline pass
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1136/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1136/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1136/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/websocket_settings_session_ceiling_and_metrics.md`
  - [x] `doc/dev/README.md` (Table of contents update)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1136/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1136/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1136/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1136/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1136/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/websocket_settings_session_ceiling_and_metrics.md`
- `doc/dev/README.md` (Table of Contents)

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID)
