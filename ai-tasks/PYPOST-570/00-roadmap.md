# Roadmap: PYPOST-570

Parent epic: [PYPOST-566](https://pypost.atlassian.net/browse/PYPOST-566) — Audit test suite
for false positives and noisy passing tests.

Depends on: [PYPOST-567](https://pypost.atlassian.net/browse/PYPOST-567) — test log inventory.

Recommended branch: `docs/PYPOST-570-log-cli-review`

## Programming Language

Python 3.10+ (same as the PyPost application codebase; see `.cursor/lsr/do-python.md`).

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] `log-cli-review.md` — quantified noise, option comparison, recommendation
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-570/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-570/20-architecture.md`

### STEP 3: Development

- `ai-tasks/PYPOST-570/log-cli-review.md`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-570/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-570/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-570/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/testing.md` — Pytest live logging section
- `ai-tasks/PYPOST-570/70-dev-docs.md`

## Related Work

- Parent: [PYPOST-566](https://pypost.atlassian.net/browse/PYPOST-566)
- Evidence: [PYPOST-567](https://pypost.atlassian.net/browse/PYPOST-567) inventory (`tests.txt` baseline)
- Error-path audit: [PYPOST-568](https://pypost.atlassian.net/browse/PYPOST-568)
- Follow-up implementation: [PYPOST-571](https://pypost.atlassian.net/browse/PYPOST-571) — CI allowlist / guardrails
