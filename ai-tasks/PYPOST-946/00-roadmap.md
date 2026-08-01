# Roadmap: PYPOST-946

## Programming Language

Python 3.10+ for pytest Qt fixture proofs. Developer docs in English Markdown.

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *N/A — no behavioral change (PYPOST-917 keyClicks fill already delivers
    per-key events; Step 4 adds signal-count assertion only)*
- [x] **STEP 4: Development**
  - [x] `test_ui_fill_via_key_clicks_emits_text_changed_per_keystroke` in
    `tests/test_ui_actions.py`; green on first run
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

- `ai-tasks/PYPOST-946/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-946/20-architecture.md`

### STEP 3: Failing Repro

- N/A — coverage-only; no red product repro

### STEP 4: Development

- `tests/test_ui_actions.py` — `textChanged` multi-emit assert on line-edit
  keyClicks fixture

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-946/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-946/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-946/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/ui_actions.md`
- `doc/dev/testing.md`
- `ai-tasks/PYPOST-946/70-dev-docs.md`
