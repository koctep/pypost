# PYPOST-389: Unit tests for stale expanded-collection ids

## Goals

When a user deletes a collection, its id may remain in persisted `expanded_collections`
settings. On the next app start or tree reload, restore logic must ignore unknown ids and still
expand valid collections. Automated tests document and guard this edge case.

## User Stories

- As a maintainer, I want a unit test for stale saved collection ids so regressions in
  `restore_tree_state` are caught in CI.
- As a user, I expect the collections tree to restore correctly even when settings contain ids
  for collections that no longer exist.

## Definition of Done

- Unit test covers `expanded_collections` containing an id not present in the current model.
- Valid collection ids in the same list are still expanded after `restore_tree_state`.
- Stale ids are left in settings (no silent pruning required for this task).
- Relevant test suite passes locally and in CI.
- Developer docs reference the test.

## Task Description

Follow-up from `ai-tasks/PYPOST-8/40-tech-debt.md`: edge-case coverage for tree state restore
when settings reference deleted collections. Implementation landed earlier (PYPOST-93); this
task formalizes PYPOST-8 closure and documentation.

## Q&A

- **Q:** Should stale ids be removed from settings automatically? **A:** Out of scope — test
  asserts current behavior (stale ids retained, restore skips them).
- **Q:** Full UI restart test? **A:** No — presenter unit test matches project conventions.
