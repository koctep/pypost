# Roadmap: PYPOST-919

**Programming language:** Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] Red naïve click+wait accepted; path
    `tests/test_agent_dialog_settle_e2e.py`
- [x] **STEP 4: Development**
  - [x] Green settle: `QTimer.singleShot` → `wait_until` on
    `activeModalWidget` → `reject()` before/during `ui_click`;
    `step=wait_dialog_after_settings_open` on timeout rewrap
  - [x] Docs: cross-links in `agent_golden_e2e.md` / `ui_wait.md`
    (harness table already had dialog settle row)
  - [x] Kept single happy-path proof (optional timeout companion
    deferred — second agent_e2e session after modal segfaulted)
- [x] **STEP 5: Code Cleanup**
  - [x] `make lint` + scoped flake8 clean; timeout markers verified;
    focused agent_e2e pass; `40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Documented reuse of `ui_wait_settled` / `ui_wait_timeout`;
    step `wait_dialog_after_settings_open`, condition
    `settings_dialog_present`, `UiWaitTimeoutError` scalars; new
    metrics/logs N/A — `50-observability.md`
- [x] **STEP 7: Review and Technical Debt**
  - [x] `60-tech-debt.md` — SAFE TO CLOSE; TD-1 Medium timeout
    companion; TD-2/TD-3 Low identity helper / shared settle helper;
    no blockers; Jira follow-ups deferred to Phase D
- [x] **STEP 8: Dev Docs**
  - [x] Dedicated `doc/dev/agent_dialog_settle.md` (Overview /
    Architecture / Usage / Configuration / Troubleshooting)
  - [x] Cross-links: `agent_e2e.md`, `agent_golden_e2e.md`,
    `ui_wait.md`, `gui_testing.md`, `settings_dialog.md`,
    `doc/dev/README.md`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-919/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-919/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_dialog_settle_e2e.py` (red naïve click+wait; see
  `20-architecture.md` failing-repro plan)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-919/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-919/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-919/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/agent_dialog_settle.md` (primary)
- Cross-links in `doc/dev/agent_e2e.md`, `agent_golden_e2e.md`,
  `ui_wait.md`, `gui_testing.md`, `settings_dialog.md`,
  `doc/dev/README.md`
