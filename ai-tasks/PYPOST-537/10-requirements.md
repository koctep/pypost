# PYPOST-537: Add direct unit tests for CollectionTreeActions

## Goals

Close tech debt from PYPOST-326/PYPOST-349: collection tree context-menu behavior is
extracted into `CollectionTreeActions`, but tests still construct a full
`CollectionsPresenter` to reach it. Direct unit tests make failures easier to localize and
reduce coupling in the test suite.

## User Stories

- As a maintainer, I want `CollectionTreeActions` tested in isolation so menu dispatch,
  rename, and delete branches can change without presenter wiring noise.
- As a CI consumer, I want fast, focused tests that assert callback and metric contracts on
  the actions class itself.

## Definition of Done

- Dedicated tests construct `CollectionTreeActions` directly (no `CollectionsPresenter`).
- Coverage includes context-menu dispatch (collection vs request, rename, new tab, delete).
- Coverage includes rename cancel, commit, and empty-name rejection callbacks.
- Coverage includes delete confirmation Yes/No branches and metric sequences.
- Existing collection-tree test modules pass after refactor.

## Task Description

Follow-up from `ai-tasks/PYPOST-326/60-tech-debt.md`. Presenter integration tests remain in
`test_collections_presenter.py`; this task adds the missing isolated layer.

### Programming Language

Python

### Functional Requirements

- Shared test harness builds `QTreeView`, `QStandardItemModel`, and injected callbacks.
- Menu tests patch `QMenu` at `collection_tree_actions` import site.
- Rename and delete dialog helpers patched at the same import site.

### Non-Functional Requirements

- No production code behavior changes.
- Tests run headless (`QT_QPA_PLATFORM=offscreen`).

### Constraints and Assumptions

- Test-only change; observability content unchanged.
- `test_collection_tree_delete_metrics.py` may keep presenter wiring (out of scope).

## Q&A

- **Q:** Replace presenter tests? **A:** No — presenter tests stay; isolated tests complement them.
- **Q:** Why a shared harness module? **A:** Avoid duplicating tree model setup across test files.
