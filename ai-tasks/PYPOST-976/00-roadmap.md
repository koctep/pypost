# Roadmap: PYPOST-976

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *N/A deliberate red — expected-green contract (PASSED on first run):
    `tests/test_ui_actions.py::test_ui_fill_via_key_clicks_session_request_body`*
- [x] **STEP 4: Development**
  - [x] *Verified contract test green on first run — no production changes
    required (`test_ui_fill_via_key_clicks_session_request_body` PASSED 7ms)*
  - [x] *Test-only task complete: POST method select → keyClicks fill on
    `REQUEST_BODY_EDIT` → `toPlainText()` assert matches architecture*
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
  - [x] *Test-only — no new logs; existing `ui_action_applied` DEBUG with
    `via_key_clicks=true` covers path; caplog deferred to PYPOST-977*
- [x] **STEP 7: Review and Technical Debt**
  - [x] *Verdict SAFE TO CLOSE; closes PYPOST-945 UT-1; caplog remains
    [PYPOST-977](https://pypost.atlassian.net/browse/PYPOST-977)*
- [x] **STEP 8: Dev Docs**
  - [x] *Cross-linked session body keyClicks smoke in
    `doc/dev/ui_actions.md` and `doc/dev/testing.md`*

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-976/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-976/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-976/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-976/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-976/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

Python 3.10+ (pytest agent e2e verification)

## Suggested branch

`test/PYPOST-976-session-body-keyclicks-smoke`
