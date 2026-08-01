# Roadmap: PYPOST-947

## Programming Language

Python 3.10+ for pytest Qt fixture proofs and agent UI actions. Developer docs
in English Markdown.

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `test_ui_fill_via_key_clicks_forwards_delay_kwarg` — red
    (`TypeError: unexpected keyword argument 'delay'`) before Step 4
- [x] **STEP 4: Development**
  - [x] `delay: int = -1` on module + session `ui_fill`; forwarded to
    `QTest.keyClicks` on opt-in path; default unchanged
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-947/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-947/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_ui_actions.py` — delay kwarg smoke (red before Step 4)

### STEP 4: Development

- `pypost/agent/ui_actions.py`
- `pypost/agent/lifecycle.py`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-947/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-947/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-947/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/ui_actions.md`
- `doc/dev/testing.md`
- `ai-tasks/PYPOST-947/70-dev-docs.md`
