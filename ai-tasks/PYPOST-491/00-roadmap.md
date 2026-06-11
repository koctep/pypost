# Roadmap: PYPOST-491

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `pypost/core/constants.py` with `HIDDEN_MASK`; updated mixins, env dialog,
        policy, and test imports; all related tests pass.
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

Python 3.10+ (same as the pypost application codebase; see `.cursor/lsr/do-python.md`).

## Related Work

- Parent feature: [PYPOST-448](https://pypost.atlassian.net/browse/PYPOST-448) (configurable
  hidden-key name logging)
- Source debt item: [PYPOST-448 technical-debt analysis](ai-tasks/PYPOST-448/60-tech-debt.md)
- Prior related task: [PYPOST-490](https://pypost.atlassian.net/browse/PYPOST-490)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-491/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-491/20-architecture.md`

### STEP 3: Development

- `pypost/core/constants.py`
- Import updates in mixins, env dialog, policy, tests

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-491/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-491/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-491/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-491/70-dev-docs.md`
- `doc/dev/hidden_variables.md`

## Task Context

- Programming language: Python
- Jira issue: PYPOST-491
- Summary: Extract HIDDEN_MASK to shared constants module
- Type: Debt (refactoring)
- Recommended branch name: `refactor/PYPOST-491-hidden-mask-constants`
