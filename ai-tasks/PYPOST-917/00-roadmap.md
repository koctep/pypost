# Roadmap: PYPOST-917

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_ui_actions.py::test_ui_fill_via_key_clicks_on_fixture`
  - [x] `tests/test_ui_actions.py::test_ui_fill_via_key_clicks_session`
- [x] **STEP 4: Development**
  - [x] Added `via_key_clicks` to `ui_fill` (default setter path + keyClicks
    branch for QLineEdit / QPlainTextEdit / QTextEdit) and mirrored on
    `AgentAppSession.ui_fill`; DEBUG log includes `via_key_clicks=%s`
  - [x] Step 3 red tests green; existing fill/setter/caplog tests still pass
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-917/50-observability.md` — documents
    `via_key_clicks` DEBUG scalar; no new test (false-path caplog in Step 4)
- [x] **STEP 7: Review and Technical Debt**
  - [x] `ai-tasks/PYPOST-917/60-tech-debt.md` — SAFE TO CLOSE; 4 unticketed
    NON-BLOCKER items (TD-1..TD-4); no Jira links (Phase D skips ticketing)
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/ui_actions.md` — opt-in `via_key_clicks` fill modes +
    troubleshooting vs `ui_send_key`
  - [x] `doc/dev/logging.md` — fill `via_key_clicks` scalar
  - [x] `ai-tasks/PYPOST-917/70-dev-docs.md`


## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python (PySide6 agent UI actions)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-917/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-917/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_ui_actions.py::test_ui_fill_via_key_clicks_on_fixture`
- `tests/test_ui_actions.py::test_ui_fill_via_key_clicks_session`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-917/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-917/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-917/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/ui_actions.md`
- `doc/dev/logging.md`
- `ai-tasks/PYPOST-917/70-dev-docs.md`
