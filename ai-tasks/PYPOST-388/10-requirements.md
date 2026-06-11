# PYPOST-388: Unit tests for tree state save/restore logic

## Goals

PYPOST-8 introduced persisting which collection nodes are expanded across restarts. That behavior
was validated manually. Automated unit tests reduce regression risk and document the expected
save/restore contract for maintainers.

## User Stories

- As a maintainer, I want unit tests for expand/collapse persistence so tree state changes are
  caught in CI without manual app restarts.
- As a user, I expect expanded collections to stay expanded after reload — tests guard that
  behavior.

## Definition of Done

- Unit tests cover saving expanded collection ids when the tree expands or collapses.
- Unit tests cover restoring expansion from saved state after the model is rebuilt.
- Unit tests cover a happy-path round trip: expand → persist → reload model → restore → UI
  expanded.
- StateManager persistence of `expanded_collections` remains covered (existing tests).
- Relevant test suite passes in CI/local `unittest` runs.

## Task Description

Follow-up from `ai-tasks/PYPOST-8/40-tech-debt.md`: tree state save/restore lacked automated
tests. Parallel work under PYPOST-10 (PYPOST-92) added presenter tests; this task closes the
PYPOST-8 debt item by verifying coverage and documenting it.

## Q&A

- **Q:** Full UI/E2E restart test required? **A:** No — presenter + StateManager unit tests
  match project conventions; E2E remains optional (PYPOST-391).
- **Q:** Edge cases (stale ids, subset expansion)? **A:** Tracked separately (PYPOST-389,
  PYPOST-391); out of scope for this debt item.
