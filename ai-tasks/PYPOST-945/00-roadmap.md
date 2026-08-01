# Roadmap: PYPOST-945

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *N/A — no behavioral change (PYPOST-917 keyClicks fill already supports
    plain/rich editors; Step 4 adds green fixture tests only)*
- [x] **STEP 4: Development**
  - [x] Isolated plain/rich fixtures + keyClicks fill tests; green on first run
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

- `ai-tasks/PYPOST-945/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-945/20-architecture.md`

### STEP 3: Failing Repro

- N/A — test-only gap; no product behavior missing (see architecture)

### STEP 4: Development

- `tests/test_ui_actions.py` — plain/rich keyClicks fixture tests

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-945/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-945/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-945/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/ui_actions.md`, `doc/dev/testing.md`
- `ai-tasks/PYPOST-945/70-dev-docs.md`

Python 3.10+ (pytest Qt fixture verification only)

## Suggested branch

`test/PYPOST-945-keyclicks-plain-rich-text`
