# PYPOST-391: Write tests to verify UI state preservation

## Goals

PYPOST-8 tree-state persistence is covered by unit tests for save/restore and stale ids.
Qt-level verification ensures the visible tree expands only saved collection nodes after
restore — guarding the user-facing behavior, not just settings writes.

## User Stories

- As a maintainer, I want a presenter test that asserts `QTreeView.isExpanded` after
  `restore_tree_state` so UI state preservation regressions are caught in CI.
- As a user, I expect only collections I left expanded to appear expanded after reload.

## Definition of Done

- Unit test covers multiple root collections where only a subset of saved ids is expanded in
  the Qt tree after `restore_tree_state`.
- Non-saved collections remain collapsed in the widget.
- Test docstring and dev docs reference PYPOST-391.
- Relevant test suite passes locally and in CI.
- PYPOST-8 tech-debt follow-up item marked resolved.

## Task Description

Follow-up from `ai-tasks/PYPOST-8/40-tech-debt.md`: complement PYPOST-388 (save/restore) and
PYPOST-389 (stale ids) with Qt-level subset expansion coverage. Parallel work under PYPOST-10
(PYPOST-95) added the same test; this task closes the PYPOST-8 debt item.

## Q&A

- **Q:** Full application restart / E2E test? **A:** Out of scope — presenter unit test with
  real `QTreeView` matches project conventions.
- **Q:** Tab state preservation? **A:** Covered separately in `tests/test_tabs_presenter.py`;
  this task is collections tree expansion only.
